#!/bin/bash
#SBATCH --job-name=aistat-drdid-full
#SBATCH --partition=gpu_b200
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=b200:4
#SBATCH --cpus-per-task=32
#SBATCH --mem=1024G
#SBATCH --time=2-00:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-DRDID-native-20261016
#SBATCH --output=/nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-DRDID-native-20261016/run-%j.log
set -euo pipefail
root="${1:?Supply the frozen root}"
manifest_sha="${2:?Supply the frozen input-manifest SHA-256}"
exec bash "$root/code/benchmarks/agentic_scientist_drdid_full_method_20261016/run_condition.sh" "$root" "$manifest_sha"
