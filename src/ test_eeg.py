from brainflow.data_filter import DataFilter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Parameters for analysis
steady_threshold = 5.0  # µV: max allowable fluctuation for steady activity
fluctuation_threshold = 50.0  # µV: min change for large fluctuations

# Load EEG data from CSV (replace 'eeg_data_test.csv' with the correct path if necessary)
eeg_data = DataFilter.read_file('eeg_data_test.csv')  # Reads the file saved earlier
eeg_data = np.array(eeg_data)  # Convert to NumPy array for easier manipulation
print("Loaded EEG Data:", eeg_data.shape)

# Function to analyze steady periods and fluctuations
def analyze_brainwave_activity(data, steady_threshold=5.0, fluctuation_threshold=50.0):
    results = []
    for channel_idx in range(data.shape[0]):
        channel_data = data[channel_idx]
        steady_segments = []
        fluctuation_comments = []

        # Analyze steady periods
        start_idx = 0
        for i in range(1, len(channel_data)):
            diff = abs(channel_data[i] - channel_data[i - 1])
            if diff > steady_threshold:
                # End current steady segment
                if i - 1 > start_idx:
                    steady_segments.append((start_idx, i - 1))
                start_idx = i

        # Handle last segment
        if start_idx < len(channel_data) - 1:
            steady_segments.append((start_idx, len(channel_data) - 1))

        # Analyze large fluctuations
        for i in range(1, len(channel_data)):
            diff = abs(channel_data[i] - channel_data[i - 1])
            if diff > fluctuation_threshold:
                fluctuation_comments.append(
                    f"Channel {channel_idx + 1}: Huge fluctuation from {channel_data[i - 1]:.2f} µV to {channel_data[i]:.2f} µV at sample {i}."
                )

        # Store results for this channel
        results.append({
            "channel": channel_idx + 1,
            "steady_segments": steady_segments,
            "fluctuations": fluctuation_comments,
        })

    return results

# Analyze EEG data
analysis_results = analyze_brainwave_activity(eeg_data)

# Output analysis results
for result in analysis_results:
    print(f"\nChannel {result['channel']}:")
    print("Steady segments (start to end sample):")
    for segment in result["steady_segments"]:
        print(f"  - {segment[0]} to {segment[1]}")
    print("Fluctuation comments:")
    for comment in result["fluctuations"]:
        print(f"  - {comment}")

# Save analysis results to CSV
steady_segments_df = pd.DataFrame([
    {"channel": r["channel"], "start": s[0], "end": s[1]}
    for r in analysis_results for s in r["steady_segments"]
])
steady_segments_df.to_csv("steady_segments.csv", index=False)

fluctuation_comments_df = pd.DataFrame([
    {"channel": r["channel"], "comment": c}
    for r in analysis_results for c in r["fluctuations"]
])
fluctuation_comments_df.to_csv("fluctuation_comments.csv", index=False)

# Visualize EEG data
offsets = [i * 100 for i in range(eeg_data.shape[0])]  # Offset each channel for visualization
for i in range(eeg_data.shape[0]):
    plt.plot(np.arange(eeg_data.shape[1]), eeg_data[i] + offsets[i], label=f"Channel {i+1}")

plt.xlabel('Time')
plt.ylabel('Amplitude (with offsets)')
plt.legend()
plt.title('EEG Data with Streams Offset')
plt.show()
