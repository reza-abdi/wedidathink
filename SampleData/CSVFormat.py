import pandas as pd

# file import
while True:
    file_path = input("Enter Filename: ")
    if file_path.endswith('.csv'):
        try:
            muse_data = pd.read_csv(file_path)
            break
        except FileNotFoundError:
            print("File not found. Please enter a CSV file.")
    else:
        print("Invalid file type. Please enter a CSV file.")

# Columns
brainwave_columns = [
    "TimeStamp", 
    "Delta_TP9", "Delta_AF7", "Delta_AF8", "Delta_TP10",
    "Theta_TP9", "Theta_AF7", "Theta_AF8", "Theta_TP10",
    "Alpha_TP9", "Alpha_AF7", "Alpha_AF8", "Alpha_TP10",
    "Beta_TP9", "Beta_AF7", "Beta_AF8", "Beta_TP10",
    "Gamma_TP9", "Gamma_AF7", "Gamma_AF8", "Gamma_TP10"
]
brainwave_data = muse_data[brainwave_columns].copy()

# Ensure the TimeStamp is in proper datetime format for aggregation. 
brainwave_data["TimeStamp"] = pd.to_datetime(brainwave_data["TimeStamp"], errors="coerce")

# Drop rows with invalid timestamps.
brainwave_data = brainwave_data.dropna(subset=["TimeStamp"])

# Calculate averages for each second / formatted.
brainwave_data["Second"] = brainwave_data["TimeStamp"].dt.hour * 3600 + brainwave_data["TimeStamp"].dt.minute * 60 + brainwave_data["TimeStamp"].dt.second

# Select only numeric columns for aggregation, dont use other ones.
numeric_columns = [
    "Delta_TP9", "Theta_TP9", "Alpha_TP9", "Beta_TP9", "Gamma_TP9"
]
brainwave_averages = brainwave_data.groupby("Second")[numeric_columns].mean()

# Name titles
output_data = brainwave_averages.rename(columns={
    "Delta_TP9": "Delta", 
    "Theta_TP9": "Theta", 
    "Alpha_TP9": "Alpha", 
    "Beta_TP9": "Beta", 
    "Gamma_TP9": "Gamma"
})

# Check if the output data is empty i.e valid but empty file
if output_data.empty:
    print("No valid data available to print.")
else:
    # Output the results to console in a nicely formatted way :)
    for second, row in output_data.iterrows():
        hours, remainder = divmod(second, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}\n"+
              f"Alpha {row['Alpha']:.3f}\n"+
              f"Beta {row['Beta']:.3f}\n"+
              f"Delta {row['Delta']:.3f}\n"+
              f"Gamma {row['Gamma']:.3f}\n"+
              f"Theta {row['Theta']:.3f}\n")
