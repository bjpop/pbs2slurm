Convert a Torque/PBS job script into SLURM notation.
----------------------------------------------------

Does not support all the syntax of PBS. 
Does not support PBS commands which span multiple lines.

The PBS file is supplied on standard input and the SLURM file is
written to standard output.

Always make a backup of your data before using this program.

Usage: pbs2slurm.py < pbs_file > slurm_file

License: BSD
Author: Bernie Pope
