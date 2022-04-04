## Prerequisite
- python2.7 (it is important to use 2.7 for MILCprompt because of the hashing algorithm changes in python 3.0)
- scipy
- pyyaml
- sqlalchemy
- sqlite3
- https://pythonhosted.org/Cheetah/ (for MILCprompts)

One easy way to install them would be simply installing `miniconda` with python=2.7 and do
```
conda install scipy pyyaml sqlalchemy sqlite3 cheetah
```

## Instructions
### Use python2 for all applications! Mixing python3 with python2 will cause inconsistencies in databases ###


Do the following for any new production runs:

1. Read `slurm_template.sh` carefully to ensure everything is fine. You might need to change `mpirun` to `srun` or other commands depending on the system. Note the scratch directory is automatically removed after each job via `rm -rf ${jobscratchdir}`, so do not store anything important in it (or you can comment out the lineand delete them manually later).
2. Edit `./run_db/run_param.yaml`. 
3. tbd...
