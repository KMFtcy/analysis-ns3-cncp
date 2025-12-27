# analysis-ns3-cncp
This is a repo of log analysis script for https://github.com/KMFtcy/ns3-cncp.

## FCT Analysis

```bash
# Analyze FCT data
uv run fct_analysis.py -m 100000 -d ./simulation_results -t 2 -s 5

```

```bash
# Draw plots
uv run draw_fct_analysis.py fct_analysis_result.txt cc_11_fct cc_11_noOQ_fct
```
