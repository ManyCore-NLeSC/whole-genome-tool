# Whole genome alignment script

This is a script that uses MA-PRALINE to prepare simultaneous MSA jobs.
Currently, the jobs are run in-process, but they will eventually be sent to
a cluster where they will be run in parallel.

The script, `wgt.py`, takes a single argument, which contains the path to a job
file in JSON format. This file contains an list of lists, with each outer list
item corresponding to a job and each inner list item corresponding to a
component of a command-line option. See the example in `input/test.json` for
more details.

The interesting part of the script is the `do_multiple_sequence_alignments`
function, which takes a list of `msa_input` objects, and returns a list of
`alignment` objects containing the finished alignments for all the jobs. It is
here where the jobs should be sent off to Constellation.

Support was also added to specify a predetermined join order tree in Newick
format, through the `--tree-file` option. If this option is not specified
MA-PRALINE will determine the join order itself through normal means. This was
used for debugging, but if it complicates the logic it can safely be removed.
