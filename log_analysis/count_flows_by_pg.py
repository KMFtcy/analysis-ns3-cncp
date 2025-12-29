from tqdm import tqdm
import argparse
import os

def format_size(bytes):
    """Format bytes in human-readable format"""
    mb = bytes / (1024 * 1024)
    gb = bytes / (1024 * 1024 * 1024)
    return f"{bytes} bytes ({mb:.2f} MB, {gb:.3f} GB)"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Count flows by priority (pg) and calculate total size')
    parser.add_argument('-d', dest='directory', action='store', default='.',
                        help='Directory containing the FCT files')
    parser.add_argument('-f', dest='files', nargs='+', default=['cc_11_fct.txt', 'cc_1_noPFC_fct.txt'],
                        help='List of FCT files to analyze (default: cc_11_fct.txt cc_1_noPFC_fct.txt)')
    parser.add_argument('-p', dest='priorities', nargs='+', type=int, default=[2, 3],
                        help='Priority values to count (default: 2 3)')
    args = parser.parse_args()

    directory = args.directory
    files = args.files
    priorities = args.priorities

    for filename in files:
        file = os.path.join(directory, filename)
        if not os.path.exists(file):
            print(f"Warning: {file} does not exist, skipping...")
            continue

        pg_stats = {pg: {'count': 0, 'total_size': 0} for pg in priorities}

        print(f'\n=== {filename} ===')

        # Count lines first for progress bar
        with open(file, 'r') as fin:
            total_lines = sum(1 for _ in fin)

        # Read with progress bar
        with open(file, 'r') as fin:
            for line in tqdm(fin, total=total_lines, desc=f'Reading {filename}', leave=False):
                fields = line.strip().split()
                if len(fields) < 13:  # BFC format (no pg field)
                    continue
                else:
                    pg = int(fields[6])
                    m_size = int(fields[7])

                if pg in pg_stats:
                    pg_stats[pg]['count'] += 1
                    pg_stats[pg]['total_size'] += m_size

        # Print results
        for pg in priorities:
            count = pg_stats[pg]['count']
            total_size = pg_stats[pg]['total_size']
            print(f'pg={pg}: {count} flows, total size = {format_size(total_size)}')
