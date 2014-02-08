#!/bin/bash
# Created: Sat Jul 27 2013 20:46:27 GMT+1000 (EST)

# Queue for the job:
#SBATCH -p main

# The name of the job:
#SBATCH --job-name="foobar"

# Maximum number of CPU cores used by the job:
#SBATCH --ntasks=10

# The amount of memory in gigabytes per process in the job:
#SBATCH --mem-per-cpu=3072

# Send yourself an email when the job (a)borts abnormally (b)egins (e)nds successfully
#SBATCH --mail-type=BEGIN
#SBATCH --mail-type=END

# The maximum running time of the job in days:hours:mins:secs
#SBATCH --time=0-3:10:2

# Run the job from the directory where it was launched:
# Note: SLURM defaults to running jobs in the directory
# where they are submitted, no need for $PBS_O_WORKDIR

# The modules to load:
module load bwa-gcc/1.2.3

# The job command(s):
bwa some arguments
some other stuff

a bit more stuff
