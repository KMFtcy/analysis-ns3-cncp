#!/usr/bin/env python3
import re
import pathlib
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl
import argparse
import numpy as np

# Set global font style
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 14,
    'font.weight': 'bold',
    'axes.labelweight': 'bold',
    'axes.titleweight': 'bold',
    'axes.labelsize': 24,
    'axes.titlesize': 22,
    'xtick.labelsize': 22,
    'ytick.labelsize': 22,
    'legend.fontsize': 18,
    'legend.title_fontsize': 20
})

def smooth_data(data, window_size=5):
    """
    Smooth data using moving average method
    """
    if len(data) < window_size:
        return data

    # Use pandas rolling method for moving average
    smoothed = data.rolling(window=window_size, center=True, min_periods=1).mean()
    return smoothed

def read_log_file(file_path, target_id=None, source_port=None, dest_port=None,
                  smooth_window=5, timestamp_start=None, timestamp_end=None):
    """
    Read log file and process lines containing [CNCP Update]
    Format: [CNCP Update] node_id sip dip sport dport rate [timestamp(ns)]
    Timestamp is optional; if not present, use line index as timestamp
    Optional: only keep data where timestamp_start <= timestamp <= timestamp_end (unit: seconds, float)
    """
    # Match format with timestamp
    pattern_with_ts = re.compile(
        r"\[CNCP Update\]\s+"
        r"(?P<node>\d+)\s+"
        r"(?P<sip>\S+)\s+"
        r"(?P<dip>\S+)\s+"
        r"(?P<sport>\d+)\s+"
        r"(?P<dport>\d+)\s+"
        r"(?P<rate>\d+(?:\.\d+)?)\s+"
        r"(?P<ts>\d+)"
    )
    # Match format without timestamp
    pattern_without_ts = re.compile(
        r"\[CNCP Update\]\s+"
        r"(?P<node>\d+)\s+"
        r"(?P<sip>\S+)\s+"
        r"(?P<dip>\S+)\s+"
        r"(?P<sport>\d+)\s+"
        r"(?P<dport>\d+)\s+"
        r"(?P<rate>\d+(?:\.\d+)?)\s*$"
    )
    
    records = []
    line_index = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Only process lines containing [CNCP Update]
            if '[CNCP Update]' in line:
                m = pattern_with_ts.search(line)
                if m:
                    # Case with timestamp
                    rec = m.groupdict()
                    node_id = int(rec["node"])
                    sip = rec["sip"]
                    dip = rec["dip"]
                    sport = int(rec["sport"])
                    dport = int(rec["dport"])
                    rate = float(rec["rate"])
                    # Convert timestamp from ns to seconds (float)
                    timestamp = float(rec["ts"]) / 1e9
                else:
                    # Case without timestamp, try matching format without timestamp
                    m = pattern_without_ts.search(line)
                    if m:
                        rec = m.groupdict()
                        node_id = int(rec["node"])
                        sip = rec["sip"]
                        dip = rec["dip"]
                        sport = int(rec["sport"])
                        dport = int(rec["dport"])
                        rate = float(rec["rate"])
                        # Use line index as timestamp (assume small interval, use index*0.001 seconds)
                        timestamp = line_index * 0.001
                    else:
                        continue

                # Apply filters if specified
                if target_id is not None and node_id != target_id:
                    continue
                if source_port is not None and sport != source_port:
                    continue
                if dest_port is not None and dport != dest_port:
                    continue
                if timestamp_start is not None and timestamp < timestamp_start:
                    continue
                if timestamp_end is not None and timestamp > timestamp_end:
                    continue
                
                records.append({
                    'node_id': node_id,
                    'sip': sip,
                    'dip': dip,
                    'sport': sport,
                    'dport': dport,
                    'rate': rate,  # Rate (bits/s)
                    'timestamp': timestamp
                })
                line_index += 1

    df = pd.DataFrame(records)

    # Apply smoothing to rate data for each 5-tuple
    if len(df) > 0 and smooth_window > 1:
        smoothed_df = []
        for key, group in df.groupby(['node_id', 'sip', 'dip', 'sport', 'dport']):
            group_sorted = group.sort_values('timestamp').copy()
            group_sorted['rate_smoothed'] = smooth_data(group_sorted['rate'], smooth_window)
            smoothed_df.append(group_sorted)
        if smoothed_df:
            df = pd.concat(smoothed_df, ignore_index=True)
    
    return df

def plot_cncp_update_rate(df, show_raw=True, output_file='cncp_all.png'):
    """
    Plot CNCP update rate curves for all 5-tuples on a single chart
    """
    if len(df) == 0:
        print("No data found")
        return
    
    # Set plotting style
    sns.set_style("whitegrid")
    plt.figure(figsize=(14, 8), dpi=300)

    # Create custom color map
    colors = plt.cm.tab20(np.linspace(0, 1, 20))

    # Group and plot by 5-tuple
    for idx, (key, group) in enumerate(df.groupby(['node_id', 'sip', 'dip', 'sport', 'dport'])):
        node_id, sip, dip, sport, dport = key
        group_sorted = group.sort_values('timestamp')
        color = colors[idx % len(colors)]

        label = f"Node {node_id} {sip}:{sport}->{dip}:{dport}"

        # Plot raw data (if enabled and available)
        if show_raw and 'rate' in group_sorted.columns:
            plt.plot(group_sorted['timestamp'], group_sorted['rate'] / 1e9, 
                    color=color, 
                    linewidth=1.0,
                    alpha=0.3,
                    label=None)

        # Plot smoothed data (if available)
        if 'rate_smoothed' in group_sorted.columns:
            plt.plot(group_sorted['timestamp'], group_sorted['rate_smoothed'] / 1e9,
                    color=color,
                    linewidth=2.5,
                    label=label)
        else:
            # If no smoothed data, plot raw data
            plt.plot(group_sorted['timestamp'], group_sorted['rate'] / 1e9,
                    color=color,
                    linewidth=2.5,
                    label=label)

    # Set chart title and labels
    plt.title('CNCP Update Rate per 5-tuple', pad=20)
    plt.xlabel('Time (s)')
    plt.ylabel('Rate (Gbps)')

    # Set grid style
    plt.grid(True, linestyle='--', alpha=0.7)

    # Show legend
    plt.legend(title='Flow (Node SIP:SPORT->DIP:DPORT)', frameon=True, framealpha=1,
               loc='best', ncol=1)

    # Adjust layout
    plt.tight_layout()

    # Save chart (high DPI)
    plt.savefig(output_file,
                dpi=300,
                bbox_inches='tight',
                pad_inches=0.1)
    plt.close()

def main():
    # Create command line argument parser
    parser = argparse.ArgumentParser(description='Plot CNCP Update rate from log file')
    parser.add_argument('-i', '--log-file', required=True, help='Path to the log file')
    parser.add_argument('-o', '--output', default='cncp_all.png', help='Output file path')
    parser.add_argument('-u', '--id', type=int, help='Filter by specific node ID')
    parser.add_argument('-s', '--source-port', type=int, help='Filter by source port')
    parser.add_argument('-d', '--dest-port', type=int, help='Filter by destination port')
    parser.add_argument('-w', '--smooth-window', type=int, default=5, help='Smoothing window size for rate data')
    parser.add_argument('--show-raw', action='store_true', help='Show raw rate data in plots')
    parser.add_argument('--timestamp-start', type=float, default=None, help='Only include records with timestamp >= this value (seconds, float)')
    parser.add_argument('--timestamp-end', type=float, default=None, help='Only include records with timestamp <= this value (seconds, float)')

    args = parser.parse_args()

    # Read log file
    print(f"Reading log file: {args.log_file}")
    print(f"Filters - ID: {args.id}, Source Port: {args.source_port}, Dest Port: {args.dest_port}")
    print(f"Smoothing window: {args.smooth_window}")
    print(f"Show raw data: {args.show_raw}")
    print(f"Timestamp range: {args.timestamp_start} ~ {args.timestamp_end} (seconds)")

    df = read_log_file(args.log_file, args.id, args.source_port, args.dest_port,
                       args.smooth_window, args.timestamp_start, args.timestamp_end)

    if len(df) == 0:
        print("No data found matching the specified criteria")
        return

    print(f"Found {len(df)} records")
    print(f"Node IDs: {sorted(df['node_id'].unique())}")
    print(f"Number of unique 5-tuples: {len(df.groupby(['node_id', 'sip', 'dip', 'sport', 'dport']))}")

    # Plot chart
    plot_cncp_update_rate(df, show_raw=args.show_raw, output_file=args.output)
    print(f"Saved plot to {args.output}")

if __name__ == "__main__":
    main()

# Usage examples:
# python draw_source_update.py -i your_log_file.log
# python draw_source_update.py -i your_log_file.log -u 4 -s 100 -d 101
# python draw_source_update.py -i your_log_file.log --timestamp-start 0.5 --timestamp-end 10.0
# python draw_source_update.py -i your_log_file.log -w 10 --show-raw