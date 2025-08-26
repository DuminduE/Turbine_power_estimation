import pandas as pd
import numpy as np
from scipy.stats import weibull_min
from scipy.optimize import fsolve
from scipy.special import gamma
from scipy.interpolate import CubicSpline

# Define the Weibull ratio equation and the turbine power curve function
def weibull_ratio_equation(k, ratio):
    """
    Defines the non-linear equation to solve for the Weibull shape parameter 'k'.
    """
    gamma_val = gamma(1 + 1/k)
    if gamma_val == 0:
        return float('inf')
    return (gamma(1 + 2/k) - (gamma_val)**2) / (gamma_val)**2 - ratio**2

def turbine_power_curve_from_data():
    """
    Creates a power curve function from provided data using a cubic spline.
    Power curve regarding Vensys 82 1.5MW is taken below. 
    """
    wind_speeds = np.array([2.5, 3, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12, 12.5, 13, 13.5, 14, 14.5, 15, 15.5, 16, 16.5, 17, 17.5, 18])
    power_outputs = np.array([26, 26, 56, 130, 243, 404, 622, 894, 1175, 1395, 1485, 1491, 1498, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500, 1500])
    power_curve_func = CubicSpline(wind_speeds, power_outputs, bc_type='natural')

    def wrapped_power_curve(speed):
        if speed < wind_speeds[0] or speed > wind_speeds[-1]:
            return 0
        return power_curve_func(speed)

    return np.vectorize(wrapped_power_curve)

# Main function to process the CSV file
def process_wind_data(file_path):
    """
    Processes a CSV file to calculate predicted power and energy,
    excluding rows where 'power_production_10m' is less than 600.
    Adds a summary row with the final average to the bottom of the output file.

    Args:
        file_path (str): The path to the CSV file.
    """
    try:
        df = pd.read_csv(file_path, header=4)
        print(f"Successfully loaded '{file_path}' with {len(df)} rows.")
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return

    # Renaming columns and ensuring proper indexing
    try:
        df.rename(columns={
            df.columns[1]: 'avg_power',
            df.columns[4]: 'windspeed_avg',
            df.columns[5]: 'wind_speed_max',
            df.columns[6]: 'wind_speed_min',
            df.columns[66]: 'power_production_10m',
            df.columns[88]: 'wind_speed_std_dev'
        }, inplace=True)
    except IndexError as e:
        print(f"Error: Not enough columns in the CSV to rename. Check your file format. {e}")
        return

    # Corrected data cleaning
    numeric_cols = ['avg_power', 'windspeed_avg', 'wind_speed_max', 'wind_speed_min', 'wind_speed_std_dev', 'power_production_10m']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

    # Filter out rows where 'power_production_10m' is less than 600
    df_filtered = df[df['power_production_10m'] >= 600].copy()
    print(f"\nFiltered out {len(df) - len(df_filtered)} rows with 'power_production_10m' less than 600.")
    
    # Check if any rows remain after filtering
    if df_filtered.empty:
        print("No rows meet the filtering criteria. No output file will be generated.")
        return

    # Initialize new columns on the filtered DataFrame
    df_filtered['predicted_avg_power_kW'] = np.nan
    df_filtered['predicted_energy_kWh'] = np.nan
    df_filtered['AssumedPowerProductionpercentage'] = np.nan

    power_curve_func = turbine_power_curve_from_data()
    interval_minutes = 10
    num_samples = 600

    for index, row in df_filtered.iterrows():
        mean_wind_speed = row['windspeed_avg']
        std_dev = row['wind_speed_std_dev']
        min_wind_speed = row['wind_speed_min']
        max_wind_speed = row['wind_speed_max']
        actual_avg_power = row['avg_power']

        if pd.isna(std_dev) or std_dev <= 0 or pd.isna(mean_wind_speed) or mean_wind_speed <= 0:
            print(f"Skipping row {index} due to invalid wind data (mean: {mean_wind_speed}, std_dev: {std_dev}).")
            continue

        try:
            ratio = std_dev / mean_wind_speed
            k_initial_guess = 2.0
            
            k = fsolve(weibull_ratio_equation, k_initial_guess, args=(ratio))[0]
            
            if k <= 0:
                print(f"Skipping row {index}: Invalid shape parameter 'k' found: {k}")
                continue
            
            lambd = mean_wind_speed / gamma(1 + 1/k)
            
            if lambd <= 0:
                print(f"Skipping row {index}: Invalid scale parameter 'lambda' found: {lambd}")
                continue

            weibull_dist = weibull_min(c=k, scale=lambd)
            wind_speed_samples = weibull_dist.rvs(size=num_samples)
            wind_speed_samples = wind_speed_samples[(wind_speed_samples >= min_wind_speed) & (wind_speed_samples <= max_wind_speed)]

            if len(wind_speed_samples) > 0:
                power_generated = power_curve_func(wind_speed_samples)
                predicted_avg_power_kW = np.mean(power_generated)
                predicted_energy_kWh = predicted_avg_power_kW * (interval_minutes / 60)

                df_filtered.at[index, 'predicted_avg_power_kW'] = predicted_avg_power_kW
                df_filtered.at[index, 'predicted_energy_kWh'] = predicted_energy_kWh

                if predicted_avg_power_kW > 0:
                    percentage = (actual_avg_power / predicted_avg_power_kW) * 100
                    df_filtered.at[index, 'AssumedPowerProductionpercentage'] = percentage

        except (ZeroDivisionError, ValueError, RuntimeError) as e:
            print(f"Could not process row {index}: {e}")
            continue

    # Calculate the final average percentage from the processed rows
    avg_percentage = df_filtered['AssumedPowerProductionpercentage'].mean()
    
    # Create the summary row DataFrame with the new column names
    summary_row = pd.DataFrame([{
        'avg_power': 'Overall Average',
        'active_power_max': avg_percentage
    }])

    # Concatenate the summary row to the bottom of the filtered DataFrame
    final_df = pd.concat([df_filtered, summary_row]).reset_index(drop=True)

    print("\n--- Summary ---")
    print(f"Average Assumed Power Production Percentage (for filtered data): {avg_percentage:.2f}%")

    output_file_path = "calculated_data.csv"
    final_df.to_csv(output_file_path, index=False)
    print(f"\nUpdated data saved to '{output_file_path}' with the summary row at the bottom.")

if __name__ == '__main__':
    file_name = "/content/SCADA_data_file.csv"
    process_wind_data(file_name)
