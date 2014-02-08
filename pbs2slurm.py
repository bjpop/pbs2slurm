#!/usr/bin/env python

'''
Convert a Torque/PBS job script into SLURM notation.

Does not support all the syntax of PBS, only a small subset commonly
used at VLSCI.

Does not support PBS commands which span multiple lines.

The PBS file is supplied on standard input and the SLURM file is
written to standard output.

Always make a backup of your data before using this program.

Usage: pbs2slurm.py < pbs_file > slurm_file

Authors: Bernie Pope (bjpope@unimelb.edu.au)

License: BSD

TODO (maybe):

   * terri queue
   * job arrays
   * job depenencies
'''

import sys
import re

# Notes about regular expression notation
# (?P<name> ...) is a named group
# (?: ...) is a non-capturing group
# \S is non-whitespace
# \s is whitespace

queue = '-q\s+(?P<queue>\S+)'
name = r'-N\s+(?P<name>\S+)'
account = r'-A\s+(?P<account>\S+)'
procs = r'-l\s+(procs|nodes)=(?P<procs>\d+)(?:\s*,\s*(tpn|ppn)\s*=\s*(?P<tasks_per_node>\d+))?'
# pvmemunit is b|kb|mb|tb, word size versions (with w) are also allowed by PBS
# but we do not support them in this script
pvmem = r'-l\s+pvmem=(?P<pvmem>\d+)(?P<pvmemunit>\w+)'
# SMP uses mem
mem = r'-l\s+mem=(?P<mem>\d+)(?P<memunit>\w+)'
# days, hours and minutes are optional in PBS notation
# although the TORQUE docs don't seem to mention days ...
walltime = r'(?P<walltime>-l\s+walltime=)((((?P<days>\d+):)?(?P<hours>\d+):)?(?P<mins>\d+):)?(?P<secs>\d+)'
email_events = r'-m\s+(?P<email_events>[abe]{1,3})'
# assume an email address is any non-empty sequence of non-whitespace characters
email_address = r'-M\s+(?P<email_address>\S+)'
# stdout and stderr redirect
outpath = r'-o\s+(?P<outpath>\S+)'
errpath = r'-e\s+(?P<errpath>\S+)'

pbs_alternatives = '|'.join([queue, name, account, procs,
                             pvmem, mem, walltime, email_events,
                             email_address, outpath, errpath])
pbs_pattern = r'#PBS\s+(?:%s)' % pbs_alternatives
workdir_pattern = r'(?P<workdir>cd\s+\$PBS\_O\_WORKDIR)'
pattern = r'(?:%s|%s)' % (pbs_pattern, workdir_pattern)
matcher = re.compile(pattern)

# convert requested memory into megabytes (the memory unit size used by SLURM)
def mem_megabytes(amount, unit):
    unit = unit.lower()
    if unit == 'b':
        return amount / (2 ** 20) 
    elif unit == 'kb':
        return amount / (2 ** 10) 
    elif unit == 'mb':
        return amount
    elif unit == 'gb':
        return amount * (2 ** 10)
    elif unit == 'tb':
        return amount * (2 ** 20)
    else:
        return None

# Process a single line from the PBS file.
# If we recognise the syntax, convert to SLURM notation,
# otherwise return the line unchanged.
job_name = 'JOB'
def process_line(line):
    matches = matcher.match(line)
    if matches is not None:
        the_queue = matches.group('queue')
        if the_queue is not None:
            if 'smp' in the_queue:
                return '#SBATCH -p main\n#SBATCH --exclusive\n'
            else:
                return '#SBATCH -p main\n'
        the_name = matches.group('name')
        if the_name is not None:
            global job_name
            job_name = the_name
            return '#SBATCH --job-name="%s"\n' % (the_name)
        the_account = matches.group('account')
        if the_account is not None:
            return '#SBATCH --account="%s"\n' % (the_account)
        the_procs = matches.group('procs')
        if the_procs is not None:
            output = '#SBATCH --ntasks=%s\n' % (the_procs)
            the_tasks_per_node = matches.group('tasks_per_node')
            if the_tasks_per_node is not None:
                output += '#SBATCH --tasks-per-node=%s\n' % the_tasks_per_node
            return output
        the_pvmem = matches.group('pvmem')
        the_pvmemunit = matches.group('pvmemunit')
        if the_pvmem is not None and the_pvmemunit is not None:
            mem = mem_megabytes(int(the_pvmem), the_pvmemunit)
            if mem is not None:
                return '#SBATCH --mem-per-cpu=%s\n' % mem
        the_mem = matches.group('mem')
        the_memunit = matches.group('memunit')
        if the_mem is not None and the_memunit is not None:
            mem = mem_megabytes(int(the_pvmem), the_pvmemunit)
            if mem is not None:
                return '#SBATCH --mem=%s\n' % (mem)
        the_walltime = matches.group('walltime')
        if the_walltime is not None:
            the_days = get_walltime_value(matches.group('days'))
            the_hours = get_walltime_value(matches.group('hours'))
            the_mins = get_walltime_value(matches.group('mins'))
            the_secs = get_walltime_value(matches.group('secs'))
            return '#SBATCH --time=%s-%s:%s:%s\n' % (the_days, the_hours, the_mins, the_secs)
        # we don't handle the "-m n" option which stops email from being sent
        the_email_events = matches.group('email_events')
        if the_email_events is not None:
            output_lines = ''
            for event in the_email_events:
                if event == 'a':
                    output_lines += '#SBATCH --mail-type=FAIL\n'
                elif event == 'b':
                    output_lines += '#SBATCH --mail-type=BEGIN\n'
                elif event == 'e':
                    output_lines += '#SBATCH --mail-type=END\n'
            if output_lines != '':
                return output_lines
        the_email_address = matches.group('email_address')
        if the_email_address is not None:
            return '#SBATCH --mail-user=%s\n' % (the_email_address)
        the_outpath = matches.group('outpath')
        if the_outpath is not None:
            return '#SBATCH --output="%s"\n' % the_outpath
        the_errpath = matches.group('errpath')
        if the_errpath is not None:
            return '#SBATCH --error="%s"\n' % the_errpath
        the_workdir = matches.group('workdir')
        if the_workdir is not None:
            return '# Note: SLURM defaults to running jobs in the directory\n# where they are submitted, no need for $PBS_O_WORKDIR\n'
    # fallthrough case, we return the line unchanged
    return line

# Walltime values for days, hours and mins may
# be undefined, this helper function makes it easy
# to check for undefined values and return 0.
def get_walltime_value(match):
    if match is None:
        return 0
    else:
        return match

# just in case we want to add some command line arguments
#def parse_args():
#    parser = ArgumentParser(
#        description='Convert a PBS/Torque job submission script to SLURM syntax.')
#    return parser.parse_args()
       
def main():
#    args = parse_args()
    for line in sys.stdin:
        sys.stdout.write(process_line(line))

if __name__ == '__main__':
    main()
