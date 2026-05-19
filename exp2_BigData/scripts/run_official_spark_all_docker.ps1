$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

docker build -t traffic-official-spark:3.5.3 -f docker/spark-official/Dockerfile .
docker run --rm `
  -v "${PWD}:/workspace" `
  -w /workspace `
  -e PYTHONPATH="/opt/spark/python:/opt/spark/python/lib/py4j-0.10.9.7-src.zip:/workspace" `
  traffic-official-spark:3.5.3 `
  python3 scripts/run_official_spark_all.py
