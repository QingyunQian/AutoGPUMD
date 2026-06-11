#!/bin/bash
#SBATCH --job-name=autogpumd
#SBATCH --output=gpumd.%j.out
#SBATCH --error=gpumd.%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00

set -euo pipefail

gpumd > gpumd.stdout 2> gpumd.stderr
