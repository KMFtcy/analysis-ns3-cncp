from tqdm import tqdm
import argparse
from datetime import datetime
import os

def get_pctl(a, p):
	i = int(len(a) * p)
	return a[i]

if __name__=="__main__":
	parser = argparse.ArgumentParser(description='')
	parser.add_argument('-p', dest='prefix', action='store', default='fct_fat', help="Specify the prefix of the fct file. Usually like fct_<topology>_<trace>")
	parser.add_argument('-s', dest='step', action='store', default='5')
	parser.add_argument('-t', dest='type', action='store', type=int, default=2, help="0: normal, 1: incast, 2: all")
	parser.add_argument('-T', dest='time_limit', action='store', type=int, default=4000000000, help="only consider flows that finish before T")
	parser.add_argument('-b', dest='bw', action='store', type=int, default=25, help="bandwidth of edge link (Gbps)")
	parser.add_argument('-d', dest='directory', action='store', default='.', help="Directory containing the FCT files")
	parser.add_argument('-m', dest='max_size', action='store', type=int, default=None, help="only consider flows with size <= max_size (bytes)")
	args = parser.parse_args()

	type = args.type
	time_limit = args.time_limit
	max_size = args.max_size
	directory = args.directory

	# Please list all the cc (together with parameters) that you want to compare.
	# For example, here we list two CC: 1. HPCC-PINT with utgt=95,AI=50Mbps,pint_log_base=1.05,pint_prob=1; 2. HPCC with utgt=95,ai=50Mbps.
	# For the exact naming, please check ../simulation/mix/fct_*.txt output by the simulation.
	CCs = [
		# 'cc_1_fct',
		'cc_1_noPFC_fct',
		# 'cc_3_fct',
		# 'cc_3_noPFC_fct',
		# 'cc_7_fct',
		# 'cc_7_noPFC_fct',
		# 'cc_8_fct',
		# 'bfc_fct',
		# 'bfc_8q_fct',
		# 'bfc_32q_fct',
		'cc_11_fct',
		# 'cc_11_0loss_fct',
		# 'cc_11_20loss_fct',
		# 'cc_11_50loss_fct',
		# 'cc_11_80loss_fct',
	]

	# Configure expected pg value for each CC
	CC_pg_config = {
		'cc_1_fct': 2,
		'cc_1_noPFC_fct': 2,
		'cc_3_fct': 2,
		'cc_3_noPFC_fct': 2,
		'cc_7_fct': 2,
		'cc_7_noPFC_fct': 2,
		'cc_8_fct': 2,
		'cc_11_fct': 3,
		'bfc_fct': 2,
		'bfc_8q_fct': 2,
		'bfc_32q_fct': 2,
	}

	step = int(args.step)
	res = [[i/100.] for i in range(0, 100, step)]
	for cc in CCs:
		file = os.path.join(directory, "%s.txt"%(cc))
		flows = []
		total_flow_size = 0
		# 先统计总行数
		with open(file, 'r') as fin:
			total_lines = sum(1 for _ in fin)
		# 再带进度条读取
		with open(file, 'r') as fin:
			for line in tqdm(fin, total=total_lines, desc=f"Reading {cc}", leave=False):
				fields = line.strip().split()
				if len(fields) < 13: # could be the result from BFC
					dport = int(fields[5])
					m_size = int(fields[7])
					start_time = int(fields[8])
					fct = int(fields[9])
					standalone_f = int(fields[10])
				else:
					dport = int(fields[5])
					pg = int(fields[6])
					m_size = int(fields[7])
					start_time = int(fields[9])
					fct = int(fields[10])
					standalone_f = int(fields[11])
				# Filter by pg value from CC_pg_config
				expected_pg = CC_pg_config.get(cc, None)
				if expected_pg is not None and pg != expected_pg:
					continue
				if type == 0 and dport != 100:
					continue
				if type == 1 and dport != 200:
					continue
				if start_time + fct >= time_limit:
					continue
				if max_size is not None and m_size > max_size:
					continue
				slow = fct / standalone_f if standalone_f > 0 else 1
				slow = max(slow, 1)
				total_flow_size += m_size
				flows.append((slow, m_size))
		print(f"CC {cc} has {len(flows)} flows")
		print(f"CC {cc} has {total_flow_size} bytes of flow size")
		flows.sort(key=lambda x: x[1])
		n = len(flows)
		for i in tqdm(range(0, 100, step), desc=f"CC {cc}", leave=False):
			l = i * n // 100
			r = (i+step) * n // 100
			d = flows[l:r]
			if not d:
				res[i//step].append(0)
				res[i//step].extend([0, 0, 0])
				continue
			fct_list = sorted([x[0] for x in d])
			res[i//step].append(d[-1][1])
			res[i//step].append(get_pctl(fct_list, 0.5))
			res[i//step].append(get_pctl(fct_list, 0.95))
			res[i//step].append(get_pctl(fct_list, 0.99))

	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	# 把输出文件也写到指定的目录下
	output_file = os.path.join(directory, f"fct_analysis_result_{timestamp}.txt")

	with open(output_file, "w") as fout:
		for item in res:
			line = "%.3f %d"%(item[0], item[1])
			i = 1
			for cc in CCs:
				line += "\t%.3f %.3f %.3f"%(item[i+1], item[i+2], item[i+3])
				i += 4
			print(line)
			fout.write(line + "\n")
	print(f"\nResult written to {output_file}")
