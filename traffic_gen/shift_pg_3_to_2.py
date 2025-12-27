#!/usr/bin/env python3
import argparse
from tqdm import tqdm

def shift_priority_3_to_2(input_filename, output_filename, size_threshold=None):
    """
    Read a traffic file and change flows with priority 3 to priority 2
    If size_threshold is provided, only change flows with size < threshold
    
    Args:
        input_filename (str): Path to the input traffic file
        output_filename (str): Path to the output traffic file
        size_threshold (float, optional): Only change priority if flow size < threshold
    """
    try:
        with open(input_filename, 'r') as infile, open(output_filename, 'w') as outfile:
            # Read the first line to get total number of flows
            first_line = infile.readline().strip()
            total_flows = int(first_line)
            print(f"Total number of flows: {total_flows}")
            
            # Write the first line (total flows count) to output file
            outfile.write(first_line + '\n')
            
            # Process each flow with progress bar
            changed_count = 0
            for line in tqdm(infile, total=total_flows, desc="Processing flows"):
                # Parse the line: src_id dst_id priority dst_port size start_time
                parts = line.strip().split()
                if len(parts) >= 5:
                    # Check if priority is 3 and change it to 2
                    if parts[2] == '3':
                        # If size_threshold is provided, only change if size < threshold
                        should_change = True
                        if size_threshold is not None:
                            try:
                                flow_size = float(parts[4])
                                should_change = flow_size < size_threshold
                            except (ValueError, IndexError):
                                # If size cannot be parsed, skip this flow
                                should_change = False
                        
                        if should_change:
                            parts[2] = '2'
                            changed_count += 1
                    
                    # Write the modified line to output file
                    outfile.write(' '.join(parts) + '\n')
                else:
                    # If line format is unexpected, write as is
                    outfile.write(line)
            
            print(f"\nSuccessfully processed {total_flows} flows")
            if size_threshold is not None:
                print(f"Changed {changed_count} flows from priority 3 to 2 (size < {size_threshold})")
            else:
                print(f"Changed {changed_count} flows from priority 3 to 2")
            print(f"Output written to: {output_filename}")
    
    except FileNotFoundError:
        print(f"Error: File {input_filename} not found")
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Shift priority 3 flows to priority 2 in traffic file')
    parser.add_argument('-i', '--input', required=True, help='Input traffic file path')
    parser.add_argument('-o', '--output', required=True, help='Output traffic file path (must be specified)')
    parser.add_argument('-s', '--size-threshold', type=float, default=None,
                        help='Only change priority if flow size < threshold (optional)')
    
    args = parser.parse_args()
    
    shift_priority_3_to_2(args.input, args.output, args.size_threshold)
