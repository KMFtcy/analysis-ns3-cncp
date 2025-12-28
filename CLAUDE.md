# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python toolkit for analyzing ns3-cncp simulation logs and generating traffic datasets. The project consists of two main components:

1. **log_analysis/**: Scripts for parsing and visualizing simulation results from ns3-cncp
2. **traffic_gen/**: Utilities for generating synthetic traffic workloads

## Development Environment

- **Python**: 3.12+ (see `.python-version`)
- **Package Manager**: `uv` (see `pyproject.toml`)
- **Dependencies**: matplotlib, pandas, seaborn, tqdm

**Important**: This project uses uv for all Python environment and dependency management. All script execution and testing must use `uv run`:

## Running Code

All scripts should be executed using `uv run`:

```bash
uv run <script_path> [arguments]
```

Example:
```bash
uv run log_analysis/fct_analysis.py -m 100000 -d ./simulation_results -t 2 -s 5
```

## Log Analysis Architecture

### Log Line Prefixes

Analysis scripts parse specific log line prefixes from ns3-cncp simulator output:

- `[CNCP Update]`: Rate allocation updates parsed by `rate_allocation.py` and `draw_source_update.py`
- `[RdmaHw Receiving]`: Receiving rate data parsed by `plot_receiving_rate.py`

### FCT (Flow Completion Time) Analysis

The FCT analysis workflow involves two steps:

1. **Analysis** (`fct_analysis.py` or `sidecar_flow_analysis.py`):
   - Reads FCT files from simulation results
   - Calculates flow completion time statistics (median, 95th, 99th percentiles)
   - Outputs `fct_analysis_result_<timestamp>.txt`
   - Key parameters:
     - `-m`: Maximum flow size filter
     - `-t`: Flow type (0=normal, 1=incast, 2=all)
     - `-s`: Step size for percentile bins
     - `-d`: Directory containing FCT files

2. **Visualization** (`draw_fct_analysis.py`):
   - Takes the analysis result file and CC algorithm names
   - Generates combined plots for median, 95th, and 99th percentile slowdown
   - Output: `fct_slowdown_all_<timestamp>.png`

**Important**: The `CCs` list in `fct_analysis.py` (lines 29-46) must be manually edited to include the congestion control algorithms you want to compare. These names must match the FCT filenames (e.g., `cc_11_fct` → `cc_11_fct.txt`).

### Sidecar Flow Analysis

`sidecar_flow_analysis.py` extends FCT analysis with CC-specific priority filtering:
- Uses `CC_pg_config` dictionary (lines 48-60) to map CC names to expected priority (pg) values
- Filters flows by matching pg values before computing statistics
- Useful for analyzing specific flow classes (e.g., sidecar flows)

### Rate Allocation Visualization

Two complementary scripts for rate allocation analysis:

1. **`rate_allocation.py`**: Per-flow rate allocation
   - Filters by node_id, IP, ports, timestamp range
   - Plots individual flow rate changes over time
   - Identifies "skipped updates" (old_rate=-1, new_rate=0)

2. **`draw_source_update.py`**: CNCP update rates
   - Plots CNCP update rates for all 5-tuples
   - Supports moving average smoothing (`-w` parameter)
   - Timestamp filtering with `--timestamp-start` and `--timestamp-end`

Both scripts expect timestamps in nanoseconds but CLI parameters use seconds (converted internally).

## Traffic Generation Architecture

### Traffic File Format

Generated traffic files use the following format:
```
<number_of_flows>
<src_id> <dst_id> <priority> <dst_port> <size_bytes> <start_time_seconds>
```

### Traffic Generator (`traffic_gen.py`)

Generates Poisson traffic patterns using CDF-based flow size distributions:
- **Distributions**: Located in `traffic_gen/dist_cdf/` (AliStorage2019, FbHdp, GoogleRPC2008, WebSearch)
- **CDF Format**: Two-column space-separated text file (size, cumulative_percentage)
- **Priority Assignment**: Size ≥ 1MB → priority 3, otherwise priority 2
- **Parameters**:
  - `-n`: Number of hosts
  - `-c`: CDF file path
  - `-l`: Load (0.0-1.0, fraction of network capacity)
  - `-b`: Link bandwidth (e.g., "10G", "25G")
  - `-t`: Simulation time (seconds)
  - `-o`: Output file

### Custom Random Number Generator

`custom_rand.py` implements:
- CDF-based random sampling with interpolation
- Average/expected value calculation from CDF
- Bidirectional mapping: value ↔ percentile

### Priority Modification Tools

Two scripts for modifying flow priorities in traffic files:
- `shift_pg_3_to_2.py`: Change priority 3 → 2
- `shift_pg_2_to_3.py`: Change priority 2 → 3

Both support optional size threshold filtering (`-s` parameter).

## Common Workflows

### Generate and visualize traffic workload:
```bash
uv run traffic_gen/traffic_gen.py -n 10 -c traffic_gen/dist_cdf/GoogleRPC2008.txt -l 0.3 -b 10G -t 1 -o traffic.txt
uv run traffic_gen/draw_workload_cdf.py traffic_gen/dist_cdf/GoogleRPC2008.txt
```

### Analyze simulation FCT results:
1. Edit `CCs` list in `log_analysis/fct_analysis.py`
2. Run analysis: `uv run log_analysis/fct_analysis.py -d ./simulation_results -m 100000`
3. Generate plots: `uv run log_analysis/draw_fct_analysis.py fct_analysis_result_<timestamp>.txt cc_11_fct cc_11_noOQ_fct`

### Visualize rate allocation:
```bash
# Rate allocation per flow
uv run log_analysis/rate_allocation.py -i log.txt -n 4 --dport 101

# CNCP update rate with smoothing
uv run log_analysis/draw_source_update.py -i log.txt -u 4 -w 10 --timestamp-start 0.5 --timestamp-end 10.0
```
