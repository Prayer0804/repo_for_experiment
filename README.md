# repo_for_experiment

This repository stores course experiment projects as separate top-level folders.
Each experiment keeps its own code, dependencies, data instructions, and
documentation inside its directory.

## Project Structure

```text
repo_for_experiment/
  exp_1YoloPic/       # Experiment 1: YOLO / image detection related project
  exp2_BigData/       # Experiment 2: traffic big data processing and analysis
```

## Experiments

### exp_1YoloPic

Image detection experiment based on the existing YOLO-related materials in this
repository. Enter the folder before running its notebooks, scripts, or model
files.

```powershell
cd exp_1YoloPic
```

### exp2_BigData

Traffic big data analysis project based on NYC TLC taxi trip records. It
contains data ingestion, Bronze/Silver/Gold processing, offline analysis,
machine learning, local stream simulation, ECharts dashboard, tests, and full
documentation.

Start here:

```powershell
cd exp2_BigData
Get-Content README.md
```

Main one-command demo:

```powershell
cd exp2_BigData
python scripts/run_all.py
```

## Notes

- Keep each experiment self-contained in its own directory.
- Do not put virtual environments, generated data, private photos, model caches,
  or large temporary outputs in the repository root.
- For new experiments, create a new top-level folder such as `exp3_ProjectName/`
  and include a local `README.md`.
