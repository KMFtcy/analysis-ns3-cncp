import sys
import random
import math
import heapq
from optparse import OptionParser
from custom_rand import CustomRand
from tqdm import tqdm

def translate_bandwidth(b):
    if b == None:
        return None
    if type(b)!=str:
        return None
    if b[-1] == 'G':
        return float(b[:-1])*1e9
    if b[-1] == 'M':
        return float(b[:-1])*1e6
    if b[-1] == 'K':
        return float(b[:-1])*1e3
    return float(b)

def poisson(lam):
    return -math.log(1-random.random())*lam

if __name__ == "__main__":
    port = 80
    parser = OptionParser()
    parser.add_option("-c", "--cdf", dest = "cdf_file", help = "the file of the traffic size cdf", default = "uniform_distribution.txt")
    parser.add_option("-n", "--nhost", dest = "nhost", help = "number of hosts")
    parser.add_option("-l", "--load", dest = "load", help = "the percentage of the traffic load to each host's egress bandwidth, by default 0.3", default = "0.3")
    parser.add_option("-b", "--bandwidth", dest = "bandwidth", help = "the bandwidth of host egress link (G/M/K), by default 10G", default = "10G")
    parser.add_option("-t", "--time", dest = "time", help = "the total run time (s), by default 10", default = "10")
    parser.add_option("-o", "--output", dest = "output", help = "the output file", default = "tmp_traffic.txt")
    options,args = parser.parse_args()

    base_t = 2000000000

    if not options.nhost:
        print("please use -n to enter number of hosts")
        sys.exit(0)
    nhost = int(options.nhost)
    load = float(options.load)
    bandwidth = translate_bandwidth(options.bandwidth)
    time = float(options.time)*1000000000 # translates to ns
    output = options.output
    if bandwidth == None:
        print("bandwidth format incorrect")
        sys.exit(0)

    fileName = options.cdf_file
    file = open(fileName,"r")
    lines = file.readlines()
    # read the cdf, save in cdf as [[x_i, cdf_i] ...]
    cdf = []
    for line in lines:
        x,y = map(float, line.strip().split(' '))
        cdf.append([x,y])

    # create a custom random generator, which takes a cdf, and generate number according to the cdf
    customRand = CustomRand()
    if not customRand.setCdf(cdf):
        print("Error: Not valid cdf")
        sys.exit(0)

    ofile = open(output, "w")

    # generate flows
    avg = customRand.getAvg()
    # avg_inter_arrival for each node: based on per-node egress bandwidth and load
    avg_inter_arrival = 1/(bandwidth*load/8./avg)*1000000000
    n_flow_estimate = int(time / avg_inter_arrival * nhost)
    n_flow = 0
    ofile.write("%d \n"%n_flow_estimate)

    # Initialize event queue: each node has its first flow arrival time
    # (time, node_id)
    event_queue = [(int(poisson(avg_inter_arrival)), i) for i in range(nhost)]
    heapq.heapify(event_queue)

    # Add progress bar
    pbar = tqdm(total=n_flow_estimate, desc="Generating flows")

    while len(event_queue) > 0:
        t, src = heapq.heappop(event_queue)
        # Check if this flow exceeds simulation time
        if t > time:
            break

        # Randomly select a destination node (different from source)
        dst = random.randint(0, nhost-1)
        while dst == src:
            dst = random.randint(0, nhost-1)

        # Generate flow size from CDF
        size = int(customRand.rand())
        if size <= 0:
            size = 1

        # Determine priority based on flow size
        pg = 2
        if size > 1000000: # if size > 1MB, set pg to 3
            pg = 3

        # Write flow to output file
        ofile.write("%d %d %d 100 %d %.9f\n"%(src, dst, pg, size, t * 1e-9))
        n_flow += 1

        # Schedule next flow for this source node
        inter_t = int(poisson(avg_inter_arrival))
        heapq.heappush(event_queue, (t + inter_t, src))

        pbar.update(1)

    pbar.close()
    ofile.seek(0)
    ofile.write("%d"%n_flow)
    ofile.close()
