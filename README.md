# analysis-ns3-cncp

This is a repo of log analysis script for <https://github.com/KMFtcy/ns3-cncp>.

**Note**: Analysis scripts read log lines with specific prefixes:
- `rate_allocation.py`: reads lines with `[CNCP Update]` prefix
- `plot_receiving_rate.py`: reads lines with `[RdmaHw Receiving]` prefix

## FCT Analysis

```bash
# Analyze FCT data
uv run fct_analysis.py -m 100000 -d ./simulation_results -t 2 -s 5

```

```bash
# Draw plots
uv run draw_fct_analysis.py fct_analysis_result.txt cc_11_fct cc_11_noOQ_fct
```

## Throughput Analysis

**Stats**: Total flow size and flow count per CC

```bash
uv run throughput_analysis.py -m 100000 -d ./simulation_results
```

## Sidecar Flow Analysis

**Stats**: FCT analysis for sidecar flows

Identifies sidecar flows using CC-specific criteria (e.g., pg value) configured in `CC_pg_config` dictionary.

```bash
uv run sidecar_flow_analysis.py -m 100000 -d ./simulation_results -t 2 -s 5
```

## Rate Allocation & Receiving Rate

**Stats**: Rate allocation and receiving rate over time

### Rate Allocation

Plots rate allocation per flow with optional smoothing.

```bash
uv run rate_allocation.py -i log.txt -n 4

uv run rate_allocation.py -i log.txt -n 4 --dport 101 --timestamp-start 2.0 --timestamp-end 5.0
```

### CNCP Update Rate

Plots CNCP update rate for all 5-tuples on a single chart.

```bash
# Plot all 5-tuples
uv run draw_source_update.py -i log.txt

# Filter by node and ports
uv run draw_source_update.py -i log.txt -u 4 -s 100 -d 101

# With smoothing window and timestamp range
uv run draw_source_update.py -i log.txt -w 10 --timestamp-start 0.5 --timestamp-end 10.0
```

### Receiving Rate

Plots receiving rate from RdmaHw Receiving log lines.

```bash
uv run plot_receiving_rate.py -i log.txt -u 4 -w 200
```
