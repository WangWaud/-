#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OD600 Transformer

This script processes data from microplate readers (OD600 measurements) and converts
it into a structured format for further analysis. It supports both CSV and Excel
file formats exported from microplate readers.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
import re
from pathlib import Path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process bacterial growth data from a plate reader CSV or Excel export."
    )
    
    parser.add_argument(
        "input_file",
        help="Path to the input file from the plate reader (CSV, XLSX, or XLS format)."
    )
    
    parser.add_argument(
        "--map",
        help="Path to the CSV or Excel file that maps wells to conditions. "
             "The file must contain 'Well' and 'Condition' columns."
    )
    
    parser.add_argument(
        "-o", "--output_file",
        default="processed_growth_data.csv",
        help="Path for the output processed CSV file. (default: %(default)s)"
    )
    
    return parser.parse_args()

def load_mapping(map_file):
    """Load the mapping file that relates wells to experimental conditions."""
    if map_file is None:
        return None
    
    # Determine the file type and read accordingly
    ext = os.path.splitext(map_file)[1].lower()
    
    try:
        if ext == '.csv':
            mapping_df = pd.read_csv(map_file)
        elif ext in ['.xlsx', '.xls']:
            mapping_df = pd.read_excel(map_file)
        else:
            print(f"Unsupported mapping file format: {ext}. Please use CSV or Excel.")
            sys.exit(1)
        
        # Verify required columns
        if 'Well' not in mapping_df.columns or 'Condition' not in mapping_df.columns:
            print("Error: Mapping file must contain 'Well' and 'Condition' columns.")
            sys.exit(1)
        
        return mapping_df
    except Exception as e:
        print(f"Error loading mapping file: {e}")
        sys.exit(1)

def extract_time_values(lines):
    """
    Extract time values from plate reader data.
    
    Parameters:
    lines -- List of strings, each representing a line in the input file
    
    Returns:
    List of floats representing time points in seconds
    """
    time_values = []
    time_line_idx = None
    
    # Find the line that contains time information
    for i, line in enumerate(lines):
        if line.startswith('Time [s]'):
            time_line_idx = i
            time_line = line.strip()
            time_parts = time_line.split(',')
            
            # Check if there is any time value in this line
            if len(time_parts) > 1 and time_parts[1].strip():
                # Only one time value in this line
                try:
                    time_values.append(float(time_parts[1].strip()))
                except ValueError:
                    print(f"Warning: Could not convert time value: {time_parts[1]}")
            break
    
    # If no explicit time values in the time line, try to find time values in cycle data
    if not time_values and time_line_idx is not None:
        all_times = []
        current_time_idx = time_line_idx
        
        while current_time_idx < len(lines):
            if lines[current_time_idx].startswith('Time [s]'):
                time_parts = lines[current_time_idx].strip().split(',')
                if len(time_parts) > 1 and time_parts[1].strip():
                    try:
                        all_times.append(float(time_parts[1].strip()))
                    except ValueError:
                        print(f"Warning: Could not convert time value: {time_parts[1]}")
                        
            # Find the next time line
            next_time_idx = None
            for i in range(current_time_idx + 1, len(lines)):
                if lines[i].startswith('Time [s]'):
                    next_time_idx = i
                    break
            
            if next_time_idx is None:
                break
                
            current_time_idx = next_time_idx
        
        time_values = all_times
    
    if not time_values:
        print("Error: Could not extract time values from the file.")
        sys.exit(1)
    
    print(f"Extracted {len(time_values)} time points.")
    return time_values

def process_csv_data(file_path):
    """Process plate reader data from CSV format."""
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        # Extract time points
        time_values = extract_time_values(lines)
        
        # Process data by cycle
        all_data = []
        cycle_count = 0
        current_cycle_data = []
        current_time = None
        
        for i, line in enumerate(lines):
            # Check if this is a time line (beginning of a cycle)
            if line.startswith('Time [s]'):
                if current_cycle_data and current_time is not None:
                    # Process the previous cycle
                    all_data.extend(process_cycle_data(current_cycle_data, current_time))
                    current_cycle_data = []
                
                # Extract time for this cycle
                parts = line.strip().split(',')
                if len(parts) > 1 and parts[1].strip():
                    try:
                        current_time = float(parts[1].strip())
                        print(f"Found time point: {current_time} seconds")
                        cycle_count += 1
                    except ValueError:
                        print(f"Warning: Could not convert time value: {parts[1]}")
                        current_time = None
            
            # Check if this is a data row (A-H)
            elif re.match(r'^[A-H],', line):
                if current_time is not None:
                    current_cycle_data.append(line)
        
        # Process the last cycle if there's any
        if current_cycle_data and current_time is not None:
            all_data.extend(process_cycle_data(current_cycle_data, current_time))
        
        # Convert to DataFrame
        if not all_data:
            print("Error: No valid data was extracted from the file.")
            sys.exit(1)
        
        print(f"Processed {len(all_data)} data points from {cycle_count} cycles.")
        return pd.DataFrame(all_data)
        
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        sys.exit(1)

def process_cycle_data(data_rows, time_value):
    """
    Process a single cycle of data.
    
    Parameters:
    data_rows -- List of strings, each representing a row of OD values
    time_value -- Float representing the time point in seconds
    
    Returns:
    List of dictionaries with Well, Time_s, Time_h, and OD values
    """
    result = []
    
    for line in data_rows:
        parts = line.strip().split(',')
        row_id = parts[0]  # A, B, C, etc.
        
        if not re.match(r'^[A-H]$', row_id):
            continue
            
        for col_idx, od_value in enumerate(parts[1:13], 1):  # 12 columns (1-12)
            if not od_value or od_value.isspace():
                continue
                
            try:
                well = f"{row_id}{col_idx}"
                od = float(od_value)
                time_h = time_value / 3600.0  # Convert seconds to hours
                
                result.append({
                    'Well': well,
                    'Time_s': time_value,
                    'Time_h': time_h,
                    'OD': od
                })
            except ValueError:
                print(f"Warning: Could not convert OD value: {od_value}")
    
    return result

def process_excel_data(file_path):
    """Process plate reader data from Excel format."""
    try:
        # Load all sheets to find which one contains the data
        xl = pd.ExcelFile(file_path)
        
        all_data = []
        
        # Try each sheet
        for sheet_name in xl.sheet_names:
            try:
                # Read the Excel sheet as raw data without headers
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                
                # Look for time points and cycle data
                time_points = []
                cycle_starts = []
                
                for idx, row in df.iterrows():
                    # Check if this row contains 'Time [s]'
                    if isinstance(row[0], str) and 'Time [s]' in row[0]:
                        # Get the time value
                        if len(row) > 1 and pd.notna(row[1]):
                            try:
                                time_value = float(row[1])
                                time_points.append(time_value)
                                cycle_starts.append(idx)
                                print(f"Found time point in Excel: {time_value} seconds at row {idx}")
                            except (ValueError, TypeError):
                                print(f"Warning: Could not convert Excel time value: {row[1]}")
                
                # If no time points found, skip this sheet
                if not time_points:
                    print(f"No time points found in sheet '{sheet_name}', skipping")
                    continue
                
                print(f"Found {len(time_points)} time points in sheet '{sheet_name}'")
                
                # Process each cycle
                for cycle_idx, start_idx in enumerate(cycle_starts):
                    time_value = time_points[cycle_idx]
                    
                    # Find where the data rows start
                    data_start_idx = None
                    for i in range(start_idx, min(start_idx + 10, df.shape[0])):
                        if isinstance(df.iloc[i, 0], str) and re.match(r'^[A-H]$', df.iloc[i, 0].strip()):
                            data_start_idx = i
                            break
                    
                    if data_start_idx is None:
                        print(f"Warning: Could not find data rows for cycle at time {time_value}")
                        continue
                    
                    # Process data rows for this cycle
                    for row_idx in range(data_start_idx, min(data_start_idx + 8, df.shape[0])):  # Max 8 rows (A-H)
                        row_id = df.iloc[row_idx, 0]
                        
                        if not isinstance(row_id, str) or not re.match(r'^[A-H]$', row_id.strip()):
                            continue
                        
                        row_id = row_id.strip()
                        
                        # Process each well in the row
                        for col_idx in range(1, min(13, df.shape[1])):
                            od_value = df.iloc[row_idx, col_idx]
                            
                            # Skip empty or non-numeric values
                            if pd.isna(od_value):
                                continue
                            
                            # Convert to float if possible
                            try:
                                od = float(od_value)
                                well = f"{row_id}{col_idx}"
                                time_h = time_value / 3600.0  # Convert seconds to hours
                                
                                all_data.append({
                                    'Well': well,
                                    'Time_s': time_value,
                                    'Time_h': time_h,
                                    'OD': od
                                })
                            except (ValueError, TypeError):
                                print(f"Warning: Could not convert OD value: {od_value}")
            
            except Exception as e:
                print(f"Warning: Error processing sheet '{sheet_name}': {e}")
                continue
        
        # Check if we found any data
        if not all_data:
            print("Error: Could not find valid plate reader data in any Excel sheet.")
            sys.exit(1)
        
        print(f"Processed {len(all_data)} data points from Excel file.")
        return pd.DataFrame(all_data)
        
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        sys.exit(1)

def merge_with_conditions(data_df, mapping_df):
    """Merge the processed data with experimental conditions."""
    if mapping_df is None:
        return data_df
    
    # Merge on the Well column
    merged_df = pd.merge(data_df, mapping_df[['Well', 'Condition']], on='Well', how='left')
    
    # Check if any wells couldn't be mapped
    unmapped = merged_df[merged_df['Condition'].isna()]['Well'].unique()
    if len(unmapped) > 0:
        print(f"Warning: The following wells have no condition mapping: {', '.join(unmapped)}")
    
    return merged_df

def main():
    """Main function to process the data."""
    # Parse command line arguments
    args = parse_args()
    
    # Check if input file exists
    if not os.path.isfile(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)
    
    # Check if mapping file exists (if provided)
    if args.map and not os.path.isfile(args.map):
        print(f"Error: Mapping file '{args.map}' does not exist.")
        sys.exit(1)
    
    # Load the mapping file if provided
    mapping_df = load_mapping(args.map) if args.map else None
    
    # Process the input file based on its format
    file_ext = os.path.splitext(args.input_file)[1].lower()
    
    if file_ext == '.csv':
        print(f"Processing CSV file: {args.input_file}")
        data_df = process_csv_data(args.input_file)
    elif file_ext in ['.xlsx', '.xls']:
        print(f"Processing Excel file: {args.input_file}")
        data_df = process_excel_data(args.input_file)
    else:
        print(f"Error: Unsupported file format '{file_ext}'. Please use CSV or Excel.")
        sys.exit(1)
    
    # Check if we have data
    if data_df.empty:
        print("Error: No data was extracted from the input file.")
        sys.exit(1)
    
    # Merge with conditions if mapping provided
    if mapping_df is not None:
        data_df = merge_with_conditions(data_df, mapping_df)
        print("Merged condition data with OD readings.")
    
    # Save the processed data
    data_df.to_csv(args.output_file, index=False)
    
    # Print summary
    wells = len(data_df['Well'].unique())
    time_points = len(data_df['Time_s'].unique())
    print(f"Processing complete. Output saved to '{args.output_file}'.")
    print(f"Processed {len(data_df)} data points from {wells} wells across {time_points} time points.")
    
    # Print column information
    print("\nOutput file column information:")
    print(f"{'Column':<10} {'Count':<10} {'Min':<15} {'Max':<15} {'Example Values':<20}")
    print("-" * 70)
    
    for col in data_df.columns:
        if col in ['Well', 'Condition']:
            unique_vals = data_df[col].unique()
            n_unique = len(unique_vals)
            example = ", ".join(map(str, unique_vals[:3])) + ("..." if n_unique > 3 else "")
            print(f"{col:<10} {n_unique:<10} {'N/A':<15} {'N/A':<15} {example:<20}")
        elif col in ['Time_s', 'Time_h', 'OD']:
            min_val = data_df[col].min()
            max_val = data_df[col].max()
            n_unique = len(data_df[col].unique())
            print(f"{col:<10} {n_unique:<10} {min_val:<15.4f} {max_val:<15.4f} {'N/A':<20}")

if __name__ == "__main__":
    main()
