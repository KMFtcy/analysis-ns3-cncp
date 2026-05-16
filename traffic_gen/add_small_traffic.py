import sys
import random
import math
import heapq
from optparse import OptionParser


def translate_bandwidth(b):
    if b is None:
        return None
    if type(b) != str:
        return None
    if b[-1] == 'G':
        return float(b[:-1]) * 1e9
    if b[-1] == 'M':
        return float(b[:-1]) * 1e6
    if b[-1] == 'K':
        return float(b[:-1]) * 1e3
    return float(b)


def poisson(lam):
    return -math.log(1 - random.random()) * lam


def drain_bg_flows(heap, nhost, bg_size, avg_inter_arrival, t_bound, outf, counter):
    """Drain all background flows with time <= t_bound from the heap."""
    while heap and heap[0][0] <= t_bound:
        t_bg, src = heapq.heappop(heap)
        dst = random.randint(0, nhost - 1)
        while dst == src:
            dst = random.randint(0, nhost - 1)
        outf.write("%d %d %d %d %d %.9f\n" % (src, dst, 2, 100, bg_size, t_bg))
        counter[0] += 1
        next_t = t_bg + poisson(avg_inter_arrival)
        heapq.heappush(heap, (next_t, src))


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input", dest="input", help="input traffic file")
    parser.add_option("-n", "--nhost", dest="nhost", help="number of hosts")
    parser.add_option("-l", "--load", dest="load", help="background traffic load", default="0.1")
    parser.add_option("-b", "--bandwidth", dest="bandwidth", help="link bandwidth (G/M/K)", default="10G")
    parser.add_option("-s", "--size", dest="size", help="background flow size in KB", default="20")
    parser.add_option("-o", "--output", dest="output", help="output file")
    options, args = parser.parse_args()

    if not options.input or not options.nhost or not options.output:
        print("Usage: add_small_traffic.py -i <input> -n <nhost> -o <output> [-l load] [-b bandwidth] [-s size_kb]")
        sys.exit(0)

    nhost = int(options.nhost)
    load = float(options.load)
    bandwidth = translate_bandwidth(options.bandwidth)
    bg_size = int(options.size) * 1024  # KB to bytes

    if bandwidth is None:
        print("bandwidth format incorrect")
        sys.exit(0)

    avg_inter_arrival = 1 / (bandwidth * load / 8.0 / bg_size)  # seconds

    with open(options.input, "r") as inf, open(options.output, "w") as outf:
        n_existing = int(inf.readline().strip())

        # Read first flow to get start time
        first_line = inf.readline().strip()
        if not first_line:
            print("No flows in input file")
            sys.exit(0)

        parts = first_line.split()
        min_time = float(parts[5])

        # Heap: (next_bg_time, host_id), one entry per host
        heap = []
        for i in range(nhost):
            t = min_time + poisson(avg_inter_arrival)
            heapq.heappush(heap, (t, i))

        total = [0]
        outf.write("%-15d\n" % 0)  # placeholder for total count

        # Process first existing flow
        drain_bg_flows(heap, nhost, bg_size, avg_inter_arrival, min_time, outf, total)
        outf.write(first_line + "\n")
        total[0] += 1

        t_existing = min_time  # default in case there's only one flow

        # Process remaining existing flows
        for line in inf:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 6:
                continue
            t_existing = float(parts[5])

            drain_bg_flows(heap, nhost, bg_size, avg_inter_arrival, t_existing, outf, total)
            outf.write(line + "\n")
            total[0] += 1

        # Write actual total count (same width as placeholder to overwrite cleanly)
        outf.seek(0)
        outf.write("%-15d" % total[0])

    print("Total flows: %d" % total[0])
