# analysis-ns3-cncp

A toolkit for [ns3-cncp](https://github.com/KMFtcy/ns3-cncp) simulator, providing log analysis tools and traffic generation utilities.

## Project Structure

```
.
├── log_analysis/          # Log analysis scripts for ns3-cncp simulation results
└── traffic_gen/           # Traffic generation utilities for creating simulation datasets
```

**Note**: Analysis scripts read log lines with specific prefixes:

- `log_analysis/rate_allocation.py`: reads lines with `[CNCP Update]` prefix
- `log_analysis/plot_receiving_rate.py`: reads lines with `[RdmaHw Receiving]` prefix

## Log Analysis

### FCT Analysis

```bash
# Analyze FCT data
uv run log_analysis/fct_analysis.py -m 100000 -d ./simulation_results -t 2 -s 5

```

```bash
# Draw plots
uv run log_analysis/draw_fct_analysis.py fct_analysis_result.txt cc_11_fct cc_11_noOQ_fct
```

### Throughput Analysis

**Stats**: Total flow size and flow count per CC

```bash
uv run log_analysis/throughput_analysis.py -m 100000 -d ./simulation_results
```

### Sidecar Flow Analysis

**Stats**: FCT analysis for sidecar flows

Identifies sidecar flows using CC-specific criteria (e.g., pg value) configured in `CC_pg_config` dictionary.

```bash
uv run log_analysis/sidecar_flow_analysis.py -m 100000 -d ./simulation_results -t 2 -s 5
```

### Rate Allocation & Receiving Rate

**Stats**: Rate allocation and receiving rate over time

#### Rate Allocation

Plots rate allocation per flow with optional smoothing.

```bash
uv run log_analysis/rate_allocation.py -i log.txt -n 4

uv run log_analysis/rate_allocation.py -i log.txt -n 4 --dport 101 --timestamp-start 2.0 --timestamp-end 5.0
```

#### CNCP Update Rate

Plots CNCP update rate for all 5-tuples on a single chart.

```bash
# Plot all 5-tuples
uv run log_analysis/draw_source_update.py -i log.txt

# Filter by node and ports
uv run log_analysis/draw_source_update.py -i log.txt -u 4 -s 100 -d 101

# With smoothing window and timestamp range
uv run log_analysis/draw_source_update.py -i log.txt -w 10 --timestamp-start 0.5 --timestamp-end 10.0
```

#### Receiving Rate

Plots receiving rate from RdmaHw Receiving log lines.

```bash
uv run log_analysis/plot_receiving_rate.py -i log.txt -u 4 -w 200
```

## Traffic Generation

*Coming soon: Tools for generating simulation traffic datasets*
