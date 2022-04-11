## Prerequisite
- python2.7 (it is important to use 2.7 for MILCprompt because of the hashing algorithm changes in python 3.0)
- scipy
- pyyaml
- sqlalchemy
- sqlite3
- https://pythonhosted.org/Cheetah/ (for MILCprompts)

One easy way to install them all would be simply installing `miniconda` with python=2.7 and do
```
conda install scipy pyyaml sqlalchemy sqlite3 cheetah
```

## Instructions
### WARNING: Use python2 for all applications! Mixing python3 with python2 will cause inconsistencies in databases ###


Do the following for any new production runs:

1. Edit `./run_db/run_param.yaml`. Here are some hints:
   * `loc`: location of the gauge field configurations. These files have to be gauge fixed and followed the format `l4864f211b600m001907m05252m6382d-Coul.835.ildg` for example.
   * `datadir`: where to save the propagators, source files, slurm bash files, slurm logs, MILC logs, and correlators. This directory must contain subdirectorys `prop`, `src`, `bash`, `slurmout`, `out`, and `corr`. For the axial project, we are not saving any propagators so the log files should be relatively small. 
   * `scratchdir`: intermediate storage for files. Correlators will be first saved to this directory before moving to the `$datadir/corr` after the job completes.
   * `pmt_file`: the MILC prompt script used for generating inputs to the MILC binary. Always try `python2 $pmt_file` and double check that the test input file looks reasonable before committing to production runs.
   * `pmt_param`: set of dictionary parameters that are needed by the `$pmt_file`. The name of each entry is to help you identify the parameters but not used in any ways in the jobs. The parameters present here depend on what are required by the `$pmt_file`.
2. Now that we have edited `run_param.yaml`, we are ready to create a running database that will control the submission of slurm jobs.
3. Read `slurm_template.sh` carefully to ensure everything is fine. You might need to change `mpirun` to `srun` or other commands depending on the system documentation. Note the scratch directory is automatically removed after each job via `rm -rf ${jobscratchdir}`, so do not store anything important in it (or you can comment out the lineand delete them manually later).
