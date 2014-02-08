#!/bin/bash
#SBATCH --ntasks=16
#SBATCH --time=0-01:00:00
#SBATCH --mem-per-cpu=1024
#SBATCH --job-name="MyTestJob"
# Note: SLURM defaults to running jobs in the directory
# where they are submitted, no need for $PBS_O_WORKDIR
module load app-name/version
mpiexec My-MPI-app
