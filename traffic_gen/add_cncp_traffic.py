#!/usr/bin/env python3
"""
Add DC-CNCP traffic to existing background traffic files.

Supports two modes:
1. Independent sender mode: DC-CNCP uses different sender (1->3)
2. Shared sender mode: DC-CNCP uses same sender (0->2) as background traffic
"""

import sys
import math
import heapq
import argparse
from pathlib import Path
from optparse import OptionParser
from custom_rand import CustomRand
from tqdm import tqdm


class Flow:
    def __init__(self, src, dst, pg, dport, size, t):
        self.src = src
        self.dst = dst
        self.pg = pg
        self.dport = dport
        self.size = size
        self.t = t

    def __str__(self):
        return f"{self.src} {self.dst} {self.pg} {self.dport} {self.size} {self.t:.9f}"


def translate_bandwidth(b):
    """Translate bandwidth string to bps."""
    if b is None:
        return None
    if not isinstance(b, str):
        return None
    if b[-1] == 'G':
        return float(b[:-1]) * 1e9
    if b[-1] == 'M':
        return float(b[:-1]) * 1e6
    if b[-1] == 'K':
        return float(b[:-1]) * 1e3
    return float(b)


def poisson(lam):
    """Generate Poisson-distributed random number."""
    import random
    return -math.log(1 - random.random()) * lam


def read_background_traffic(filepath):
    """Read background traffic file and return list of Flow objects."""
    flows = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
        # First line is number of flows
        for line in lines[1:]:
            parts = line.strip().split()
            if len(parts) >= 6:
                src = int(parts[0])
                dst = int(parts[1])
                pg = int(parts[2])
                dport = int(parts[3])
                size = int(parts[4])
                t = float(parts[5])
                flows.append(Flow(src, dst, pg, dport, size, t))
    return flows


def generate_cncp_traffic(nhost, load, bandwidth, time, cdf_file, src, dst,
                          start_time_offset=0.0, base_time=2000000000):
    """
    Generate DC-CNCP traffic flows.

    Args:
        nhost: Number of hosts (not used for single flow, kept for compatibility)
        load: Traffic load (0.0-1.0)
        bandwidth: Link bandwidth in bps
        time: Simulation time in seconds
        cdf_file: Path to CDF file
        src: Source node ID
        dst: Destination node ID
        start_time_offset: Offset to add to flow start times (seconds)
        base_time: Base time in nanoseconds

    Returns:
        List of Flow objects
    """
    import random

    # Read CDF
    with open(cdf_file, 'r') as f:
        lines = f.readlines()
        cdf = []
        for line in lines:
            x, y = map(float, line.strip().split(' '))
            cdf.append([x, y])

    # Create custom random generator
    customRand = CustomRand()
    if not customRand.setCdf(cdf):
        print("Error: Not valid cdf")
        sys.exit(1)

    # Generate flows
    flows = []
    avg = customRand.getAvg()
    avg_inter_arrival = 1 / (bandwidth * load / 8.0 / avg) * 1000000000
    n_flow_estimate = int(time * 1e9 / avg_inter_arrival)

    t = base_time
    flow_count = 0

    with tqdm(total=n_flow_estimate, desc=f"Generating CNCP traffic (src={src}->dst={dst})") as pbar:
        while True:
            inter_t = int(poisson(avg_inter_arrival))
            t += inter_t

            if t > base_time + time * 1e9:
                break

            size = int(customRand.rand())
            if size <= 0:
                size = 1

            # Priority: >= 1MB -> pg 3, else pg 2
            pg = 2
            if size > 1000000:
                pg = 3

            # Add offset to start time
            start_time = t * 1e-9 + start_time_offset

            flows.append(Flow(src, dst, pg, 100, size, start_time))
            flow_count += 1
            pbar.update(1)

    return flows


def merge_flows(background_flows, cncp_flows):
    """Merge background and CNCP flows, sort by start time."""
    all_flows = background_flows + cncp_flows
    all_flows.sort(key=lambda f: f.t)
    return all_flows


def write_traffic_file(flows, output_path):
    """Write flows to traffic file."""
    with open(output_path, 'w') as f:
        f.write(f"{len(flows)} \n")
        for flow in flows:
            f.write(str(flow) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Add DC-CNCP traffic to background traffic',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Independent sender mode: CNCP uses nodes 1->3
  python add_cncp_traffic.py -i generated_traffic/web_0.1.txt -o web_0.1_cncp.txt \\
      --cncp-load 0.5 --mode independent -c dist_cdf/WebSearch_distribution.txt

  # Shared sender mode: CNCP also uses nodes 0->2
  python add_cncp_traffic.py -i generated_traffic/web_0.1.txt -o web_0.1_cncp.txt \\
      --cncp-load 0.5 --mode shared -c dist_cdf/WebSearch_distribution.txt
        """
    )

    parser.add_argument('-i', '--input', required=True,
                        help='Input background traffic file')
    parser.add_argument('-o', '--output', required=True,
                        help='Output traffic file with CNCP traffic added')
    parser.add_argument('--cncp-load', type=float, default=0.5,
                        help='CNCP traffic load (default: 0.5)')
    parser.add_argument('--mode', choices=['independent', 'shared'],
                        default='independent',
                        help='Traffic mode: independent (different sender) or shared (same sender)')
    parser.add_argument('-c', '--cdf', dest='cdf_file',
                        default='dist_cdf/WebSearch_distribution.txt',
                        help='CDF file for CNCP traffic size distribution')
    parser.add_argument('-b', '--bandwidth', dest='bandwidth',
                        default='10G',
                        help='Link bandwidth (default: 10G)')
    parser.add_argument('-t', '--time', dest='time', type=float,
                        default=10.0,
                        help='Simulation time in seconds (default: 10.0)')
    parser.add_argument('--start-offset', type=float, default=0.0,
                        help='Offset for CNCP traffic start time in seconds (default: 0.0)')
    parser.add_argument('--src', type=int, default=1,
                        help='CNCP source node (default: 1, for independent mode)')
    parser.add_argument('--dst', type=int, default=3,
                        help='CNCP destination node (default: 3, for independent mode)')
    parser.add_argument('--no-cncp', action='store_true',
                        help='Only output background traffic without adding CNCP traffic')

    args = parser.parse_args()

    # Check input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)

    # Check CDF file exists
    cdf_path = Path(args.cdf_file)
    if not cdf_path.exists():
        # Try relative to script directory
        script_dir = Path(__file__).parent
        cdf_path = script_dir / args.cdf_file
        if not cdf_path.exists():
            print(f"Error: CDF file '{args.cdf_file}' not found")
            sys.exit(1)

    # Parse bandwidth
    bandwidth = translate_bandwidth(args.bandwidth)
    if bandwidth is None:
        print(f"Error: Invalid bandwidth format '{args.bandwidth}'")
        sys.exit(1)

    print(f"Processing: {args.input}")
    print(f"Mode: {args.mode}")
    print(f"CNCP Load: {args.cncp_load}")

    # Read background traffic
    print("Reading background traffic...")
    bg_flows = read_background_traffic(args.input)
    print(f"  Background flows: {len(bg_flows)}")

    # Determine CNCP source/destination based on mode
    if args.mode == 'independent':
        cncp_src = args.src
        cncp_dst = args.dst
    else:  # shared mode
        # Use same sender as background traffic (infer from first flow)
        if len(bg_flows) > 0:
            cncp_src = bg_flows[0].src
            cncp_dst = bg_flows[0].dst
        else:
            cncp_src = 0
            cncp_dst = 2

    # Generate CNCP traffic (if not disabled)
    if args.no_cncp:
        print("Skipping CNCP traffic generation (--no-cncp flag set)")
        cncp_flows = []
    else:
        print(f"Generating CNCP traffic: {cncp_src} -> {cncp_dst}")
        cncp_flows = generate_cncp_traffic(
            nhost=4,  # Dumbbell topology has 4 hosts
            load=args.cncp_load,
            bandwidth=bandwidth,
            time=args.time,
            cdf_file=str(cdf_path),
            src=cncp_src,
            dst=cncp_dst,
            start_time_offset=args.start_offset
        )
        print(f"  CNCP flows: {len(cncp_flows)}")

    # Merge flows
    all_flows = merge_flows(bg_flows, cncp_flows)
    print(f"Total flows: {len(all_flows)}")

    # Write output
    write_traffic_file(all_flows, args.output)
    print(f"Output written to: {args.output}")

    # Print statistics
    if len(all_flows) > 0:
        print("\nFlow Statistics:")
        print(f"  Time range: {all_flows[0].t:.6f}s - {all_flows[-1].t:.6f}s")
        src_dst_pairs = {}
        for f in all_flows:
            pair = (f.src, f.dst)
            src_dst_pairs[pair] = src_dst_pairs.get(pair, 0) + 1
        print("  Flow distribution:")
        for (src, dst), count in sorted(src_dst_pairs.items()):
            print(f"    {src}->{dst}: {count} flows")


if __name__ == "__main__":
    main()
