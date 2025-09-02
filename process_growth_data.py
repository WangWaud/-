import pandas as pd
import re
import argparse
import sys

def parse_plate_reader_data(file_path: str) -> pd.DataFrame:
    """
    Parses raw plate reader data from a CSV file exported from the instrument.

    Args:
      file_path (str): The path to the input CSV file.

    Returns:
      A DataFrame with 'Well', 'Time_s', and 'OD' columns.
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    all_data = []
    current_time = None

    for line in lines:
        if line.startswith('Time [s]'):
            try:
                current_time = float(line.split(',')[1])
            except (ValueError, IndexError):
                current_time = None
        elif current_time is not None and re.match(r'^[A-H],', line): # Support full 96-well plate
            parts = line.strip().split(',')
            row_letter = parts[0]
            od_values = [float(p) if p else None for p in parts[1:13]]

            for i, od in enumerate(od_values):
                well = f"{row_letter}{i+1}"
                all_data.append([well, current_time, od])

    if not all_data:
        print("[!] Error: No data could be parsed. Please check the input file format.")
        sys.exit(1)
        
    df = pd.DataFrame(all_data, columns=['Well', 'Time_s', 'OD'])
    return df

def add_conditions_from_map(df: pd.DataFrame, map_file_path: str) -> pd.DataFrame:
    """
    Adds a 'Condition' column to the DataFrame by merging it with a custom mapping file.

    Args:
      df (pd.DataFrame): The input DataFrame from parsing.
      map_file_path (str): The path to the CSV file containing the well-to-condition map.

    Returns:
      The DataFrame with the added 'Condition' column.
    """
    try:
        map_df = pd.read_csv(map_file_path)
    except FileNotFoundError:
        print(f"[!] Error: The mapping file was not found at '{map_file_path}'")
        sys.exit(1)

    # Check for required columns in the mapping file
    if 'Well' not in map_df.columns or 'Condition' not in map_df.columns:
        print("[!] Error: The mapping file must contain 'Well' and 'Condition' columns.")
        sys.exit(1)
        
    # Merge the data with the conditions map
    # A left merge ensures we keep all OD data, even if a well is missing from the map.
    merged_df = pd.merge(df, map_df, on='Well', how='left')
    
    # Check if any conditions are missing after the merge
    if merged_df['Condition'].isnull().any():
        missing_wells = merged_df[merged_df['Condition'].isnull()]['Well'].unique()
        print(f"[!] Warning: No conditions were found in the map for the following wells: {', '.join(missing_wells)}")
        
    return merged_df

def main():
    """Main function to parse arguments and run the data processing pipeline."""
    parser = argparse.ArgumentParser(
        description="Process bacterial growth data from a plate reader CSV export.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input CSV file from the plate reader."
    )
    parser.add_argument(
        "--map",
        type=str,
        required=True, # This makes the map file a mandatory argument
        help="[REQUIRED] Path to the CSV file that maps wells to conditions.\n"
             "The file must contain 'Well' and 'Condition' columns."
    )
    parser.add_argument(
        "-o", "--output_file",
        type=str,
        default="processed_growth_data.csv",
        help="Path for the output processed CSV file. (default: processed_growth_data.csv)"
    )

    args = parser.parse_args()

    print(f"[*] Reading and parsing data from '{args.input_file}'...")
    raw_df = parse_plate_reader_data(args.input_file)

    print(f"[*] Applying experimental conditions from '{args.map}'...")
    processed_df = add_conditions_from_map(raw_df, args.map)
    
    processed_df['Time_h'] = processed_df['Time_s'] / 3600

    final_df = processed_df[['Well', 'Time_s', 'Time_h', 'OD', 'Condition']].dropna(subset=['OD'])
    
    try:
        final_df.to_csv(args.output_file, index=False)
        print(f"[+] Successfully processed data and saved to '{args.output_file}'")
    except Exception as e:
        print(f"[!] Error saving file: {e}")


if __name__ == "__main__":
    main()