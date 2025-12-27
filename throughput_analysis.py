from tqdm import tqdm
import argparse
from datetime import datetime
import os

if __name__=="__main__":
	parser = argparse.ArgumentParser(description='')
	parser.add_argument('-p', dest='prefix', action='store', default='fct_fat', help="Specify the prefix of the fct file. Usually like fct_<topology>_<trace>")
	parser.add_argument('-t', dest='type', action='store', type=int, default=2, help="0: normal, 1: incast, 2: all")
	parser.add_argument('-T', dest='time_limit', action='store', type=int, default=4000000000, help="only consider flows that finish before T")
	parser.add_argument('-d', dest='directory', action='store', default='.', help="Directory containing the FCT files")
	parser.add_argument('-m', dest='min_size', action='store', type=int, required=True, default=0, help="only consider flows with size >= min_size (bytes)")
	args = parser.parse_args()

	type = args.type
	time_limit = args.time_limit
	min_size = args.min_size
	directory = args.directory

	# Please list all the cc (together with parameters) that you want to compare.
	# For the exact naming, please check ../simulation/mix/fct_*.txt output by the simulation.
	CCs = [
		'cc_1_fct',
		# 'cc_1_noPFC_fct',
		'cc_3_fct',
		# 'cc_3_noPFC_fct',
		'cc_7_fct',
		# 'cc_7_noPFC_fct',
		# 'cc_8_fct',
		'cc_11_fct',
		'cc_11_noOQ_fct',
        'bfc_fct',
		# 'cc_11_0loss_fct',
		# 'cc_11_20loss_fct',
		# 'cc_11_50loss_fct',
		# 'cc_11_80loss_fct',
		# 'bfc_8q_fct',
		# 'bfc_32q_fct',
	]

	results = {}
	for cc in tqdm(CCs, desc="Processing CCs"):
		file = os.path.join(directory, "%s.txt"%(cc))
		if not os.path.exists(file):
			print(f"Warning: {file} not found, skipping")
			results[cc] = (0, 0)
			continue
		
		total_size = 0
		flow_count = 0
		
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
					m_size = int(fields[7])
					start_time = int(fields[9])
					fct = int(fields[10])
					standalone_f = int(fields[11])
				
				if type == 0 and dport != 100:
					continue
				if type == 1 and dport != 200:
					continue
				if start_time + fct >= time_limit:
					continue
				if m_size < min_size:
					continue
				
				total_size += m_size
				flow_count += 1
		
		results[cc] = (total_size, flow_count)

	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	output_file = os.path.join(directory, f"throughput_analysis_result_{timestamp}.txt")

	with open(output_file, "w") as fout:
		header = "CC\tTotal_Size(bytes)\tFlow_Count"
		print(header)
		fout.write(header + "\n")
		
		for cc in CCs:
			total_size, flow_count = results[cc]
			line = f"{cc}\t{total_size}\t{flow_count}"
			print(line)
			fout.write(line + "\n")
	
	print(f"\nResult written to {output_file}")
	print(f"Min size filter: >= {min_size} bytes")

