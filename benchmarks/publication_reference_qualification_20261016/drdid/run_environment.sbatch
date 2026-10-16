#!/bin/bash
#SBATCH --job-name=aistat-drdid-env
#SBATCH --qos=normal
#SBATCH --partition=day
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-DRDID-source-20261016
#SBATCH --output=/nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-DRDID-source-20261016/setup-%j.log
set -euo pipefail
printf '%s  %s\n' b0e2e906ee9e2bcfe696445baaf456f7ca75592f3f8ba79af9c1de7e8ce3d602 \
  prepare_environment.sh | sha256sum --check
exec bash prepare_environment.sh \
  /nfs/roberts/project/pi_fl426/yz2324/AI-Statistician-DRDID-source-20261016 \
  a326723a51caa33152cb2c624cd7515d366d832d45454ed130a98e630b1c17c3
