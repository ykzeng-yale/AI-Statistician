#!/bin/bash
#SBATCH --job-name=aistat-flashnext-native-review
#SBATCH --account=pi_fl426
#SBATCH --qos=normal
#SBATCH --partition=gpu_b200
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=b200:4
#SBATCH --cpus-per-task=32
#SBATCH --mem=1024G
#SBATCH --time=2-00:00:00
#SBATCH --dependency=afterok:29733204
#SBATCH --no-requeue
#SBATCH --chdir=/nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-Qwen38-FlashNext-20261016/assessment-native-20261016
#SBATCH --output=/nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-Qwen38-FlashNext-20261016/assessment-native-20261016/review-%j.log
set -euo pipefail
printf '%s  %s\n' b85dfcb696e2c11eac94402a7b4074aaf085d28645ade6b1a6b970e56450c00a \
  code/benchmarks/publication_assessment_flashnext_20261016/run_assessment.sh | sha256sum --check
exec bash code/benchmarks/publication_assessment_flashnext_20261016/run_assessment.sh \
  /nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-Qwen38-FlashNext-20261016/assessment-native-20261016 \
  /nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-Qwen38-FlashNext-20261016 \
  /nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-Qwen38-27B-20261015 \
  3b901c3d8f3f24c4b6d595d8975576010f41e2ac18898ab644a58e8c42c7f338
