#!/bin/bash

# A test harness for the pbs2slurm program.
# input test cases must end in .pbs suffix, and must be
# accompanied with an expected .slurm output.
# Tests allow command line arguments, although the pbs2slurm 
# program doesn't have any at the moment.


# Authors: Bernie Pope, 2013.

#set -x

PROGRAM='./pbs2slurm.py'
OUTPUT_FILE_STDOUT='/tmp/pbs2slurm_stdout'
OUTPUT_FILE_STDERR='/tmp/pbs2slurm_stderr'
CASES='tests/*.pbs'

runtests () {
   # $1 is the list of test files (glob pattern)
   # $2 is the exit status to check for
   total=0
   pass=0
   for pbs_script in $1; do
      passed_test=1
      test_name=`basename $pbs_script .pbs`
      test_dir=`dirname $pbs_script`
      full_test_name="${test_dir}/${test_name}"
      args=''

      echo "testing $full_test_name"

      # check for a file providing command line arguments
      if [ -f ${full_test_name}.args ]; then
          args=`cat ${full_test_name}.args`
      fi

      # run the slurm2pbs program on the test input and save stdout and stderr to files
      (cat $pbs_script | $PROGRAM $args > $OUTPUT_FILE_STDOUT) >& $OUTPUT_FILE_STDERR
      # save the exit status of the program
      exit_status=$?
      # compare the exit status with what was expected.
      if [ $2 = exit_with_zero ]; then
         # pbs2slurm returned non-zero when it should have been zero
         if [ $exit_status -ne 0 ]; then
            echo "*** pbs2slurm failed ${full_test_name}.pbs on exit status."
            echo "    Zero exit status was expected but not found."
            passed_test=0
         fi
      elif [ $2 = exit_with_non_zero ]; then
         # pbs2slurm returned zero when it should have been non-zero
         if [ $exit_status -eq 0 ]; then
            echo "*** pbs2slurm failed ${full_test_name}.pbs on exit status."
            echo "    Non-zero exit status was expected but not found."
            passed_test=0
         fi
      fi
      # compare the stdout of pbs2slurm to the expected stdout, if such a file exists
      expected_stdout="${full_test_name}.slurm"
      if [ -f "$expected_stdout" ]; then
         diff "$OUTPUT_FILE_STDOUT" "$expected_stdout" > /dev/null
         if [ $? -ne 0 ]; then 
            echo "*** pbs2slurm failed ${full_test_name}.pbs"
            passed_test=0
         fi
      fi
      # compare the stderr of the pbs2slurm to the expected sterr, if such a file exists
      expected_stderr="${full_test_name}.stderr"
      if [ -f "$expected_stderr" ]; then
         diff $OUTPUT_FILE_STDERR "$expected_stderr" > /dev/null
         if [ $? -ne 0 ]; then
            echo "*** pbs2slurm failed ${full_test_name}.pbs on expected standard error."
            passed_test=0
         fi
      fi
      # count the total tests and the passed tests.
      total=`expr $total + 1`
      pass=`expr $pass + $passed_test`
   done

   echo "Passed ${pass}/${total} tests"
}

# run all the test cases, first the cases that should be rejected by
# pbs2slurm and second the cases that should be allowed by pbs2slurm.
runtests "$CASES" exit_with_zero

# clean up temporary files when we exit
trap "/bin/rm -f $OUTPUT_FILE_STDOUT $OUTPUT_FILE_STDERR" EXIT
