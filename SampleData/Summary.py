import pandas as pd
import numpy as np
import os
import datetime

# Prompt for file input
file_path = input("Enter Filename: ")

# Load CSV with data type adjustments or low_memory=False
try:
    # Attempt to specify types for problematic columns
    muse_data = pd.read_csv(file_path, dtype={38: 'float'}, low_memory=False)
except ValueError as e:
    print(f"Warning: {e}. Loading with low_memory=False.")
    muse_data = pd.read_csv(file_path, low_memory=False)

# Rest of your analysis script goes here
print(muse_data.head())
data = pd.read_csv(file_path)

# Define parameters for filtering movement and poor signal quality
gyro_threshold_degrees = 30.0  # Threshold for significant movement in degrees/second
hsi_good_contact_value = 1.0   # Value indicating good contact for HSI columns (ENSURES USER HAS HEADSET MAKING CONTACT)

# Filter out rows where there is significant movement based on gyroscope data
filtered_data = data[
    (abs(data['Gyro_X']) < gyro_threshold_degrees) &
    (abs(data['Gyro_Y']) < gyro_threshold_degrees) &
    (abs(data['Gyro_Z']) < gyro_threshold_degrees)
]

# Further filter rows where HSI indicates poor signal contact (i.e., poor quality readings)
filtered_data = filtered_data[
    (filtered_data['HSI_TP9'] == hsi_good_contact_value) &
    (filtered_data['HSI_AF7'] == hsi_good_contact_value) &
    (filtered_data['HSI_AF8'] == hsi_good_contact_value) &
    (filtered_data['HSI_TP10'] == hsi_good_contact_value)
]

# Define thresholds and parameters for spike analysis
threshold_change = 0.50  # Significant spike threshold (change ratio)
minimum_duration = 15     # Minimum duration (number of rows) for a valid spike

# Function to analyze brainwave spikes with longer sustained periods
def analyze_brainwaves(data, brainwave, threshold, min_duration):
    results = []
    start_timestamp = None
    start_value = None
    max_value = None
    spike_values = []

    for i, row in data.iterrows():
        current_value = row[brainwave]
        timestamp = row["TimeStamp"]

        if spike_values:
            # Check if the spike continues
            if (current_value - start_value) / abs(start_value) >= threshold:
                spike_values.append(current_value)
                max_value = max(max_value, current_value)
            else:
                # End spike if conditions are met
                if len(spike_values) >= min_duration:
                    end_timestamp = timestamp
                    average_value = np.mean(spike_values)
                    results.append({
                        "Timestamp": f"{start_timestamp} to {end_timestamp}",
                        "Brain Wave Type": brainwave,
                        "Spike Value": start_value,
                        "Max Value": max_value,
                        "Ending Value": current_value,
                        "Average Value": average_value,
                        "Summary": f"From {start_timestamp} to {end_timestamp}, {brainwave} spiked significantly, indicating heightened activity."
                    })
                spike_values = []
                start_value = None
        else:
            # Start a new spike if a significant change is detected
            if start_value is None or (current_value - start_value) / abs(start_value) >= threshold:
                start_timestamp = timestamp
                start_value = current_value
                max_value = current_value
                spike_values.append(current_value)

    return results

# Analyze all brainwaves
brainwave_columns = ['Delta_AF8', 'Delta_TP10', 'Theta_TP9', 'Theta_AF8', 'Theta_TP10', 'Alpha_TP9', 'Alpha_AF8', 'Alpha_TP10', 'Beta_TP9', 'Beta_AF8', 'Beta_TP10', 'Gamma_TP9', 'Gamma_AF8', 'Gamma_TP10']
summary = []

for wave in brainwave_columns:
    if wave in filtered_data.columns:
        summary.extend(analyze_brainwaves(filtered_data, wave, threshold_change, minimum_duration))

if summary:
    summary_df = pd.DataFrame(summary)
        # Format the results into a DataFrame
    summary_df = pd.DataFrame(summary)

    # Save the summary to a new CSV file
    output_directory = "/Users/loganhindley/Documents/natHacks24/"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_filtered_movement = os.path.join(output_directory, f"brainwave_output_{current_time}.csv")
    summary_df.to_csv(output_file_filtered_movement, index=False)

    # Print the summary in the desired format
    for _, row in summary_df.iterrows():
        print(
            f"Timestamp: {row['Timestamp']}, Brain Wave Type: {row['Brain Wave Type']}, "
            f"Spike Value: {row['Spike Value']}, Max Value: {row['Max Value']}, "
            f"Ending Value: {row['Ending Value']}, Average Value: {row['Average Value']}. "
            f"Summary: {row['Summary']}"
        )
else:
    print("No significant brainwave spikes detected based on the input file.")
