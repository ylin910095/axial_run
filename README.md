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

## Test before production runs!
Before following the instructions below, go to ```./test_scripts``` to perform tests using ```example_slurm.sh```. Then compare the correlator and log files it generates to the ones in ```./test_scripts/example_out``` to make sure nothing funny going on! You can diff the correlator files easily using ```python2 ./test_scripts/util/diffFloat.py corr1 corr2```. 


## Instructions
### WARNING: Use python2 for all applications! Mixing python3 with python2 will cause inconsistencies in databases ###


Do the following for any new production runs:

1. Edit `./run_db/run_param.yaml`. Here are some hints:
   * `loc`: location of the gauge field configurations. These files have to be gauge fixed and followed the format `l4864f211b600m001907m05252m6382d-Coul.835.ildg` for example.
   * `datadir`: where to save the propagators, source files, slurm bash files, slurm logs, MILC logs, and correlators. This directory must contain subdirectorys `prop`, `src`, `bash`, `slurmout`, `out`, and `corr`. For the axial project, we are not saving any propagators so the log files should be relatively small. 
   * `scratchdir`: intermediate storage for files. Correlators will be first saved to this directory before moving to the `$datadir/corr` after the job completes.
   * `pmt_file`: the MILC prompt script used for generating inputs to the MILC binary. Always try `python2 $pmt_file` and double check that the test input file looks reasonable before committing to production runs.
   * `pmt_param`: set of dictionary parameters that are needed by the `$pmt_file`. The name of each entry is to help you identify the parameters but not used in any ways in the jobs. The parameters present here depend on what are required by the `$pmt_file`.
   * `milcbin`: MILC binary. Put this under `./bin/` directory (most likely I will compile this for you).

2. Now that we have edited `run_param.yaml`, we are ready to create a running database that will control the submission of slurm jobs. This can be done by doing (use python2! Or the database will be messed up)

    ```console
    foo@bar:~/axial_run$ cd run_db
    foo@bar:~/axial_run/run_db$ python2 init_run_db.py
    init_run_db.py usage: db_name run_param_yaml gauge_checksum
    ```

      Three arguments:
      * `db_name`: self-explanatory. You can reuse the exisiting database.
      * `run_param_yaml`: the yaml file you just edited.
      * `gauge_checksum`: assigning a unique checksum to each gauge configuration if 1, else skip (nan checksum). This is a DIFFERENT checksum than the one calculated in MILC. The original goal was to prevent a project from using two different gauge-fixed configurations. However, the current implementation is slow for large lattices so I usually skip it.
      
      The typical usage is then
    ```console
    foo@bar:~/axial_run/run_db$ python2 init_run_db.py somethingsomething.sqlite run_param.yaml 0
    ```

3. Read `slurm_template.sh` carefully to ensure everything is fine. You might need to change `mpirun` to `srun` or other commands depending on the system documentation. Note the scratch directory is automatically removed after each job via `rm -rf ${jobscratchdir}`, so do not store anything important in it (or you can comment out the line and delete them manually later).

4. Finally, stars are aligned for job submission, well, almost. You might want to do a sanity check first. The main file we are using is, well, `main.py`. It has the usage
 
    ```console
    foo@bar:~/axial_run$ python main.py
    main.py usage: db_name slurm_template [debug]
    ```
      * `db_name`: the running database you created earilier. 
      * `slurm_template`: `slurm_template.sh` you just read through.
      * `debug`: optional. If `debug = 1`, it will not submit any jobs and alter the running database. Instead, it will go through one entry in the todo-list in the database and create a slurm bash file in the directory you specified earlier in the yaml file. You can then maunally submit this bash job to see if the job runs fine. 
      
      So we first do a debug run by 
    ```console
    foo@bar:~/axial_run$ python2 main.py ./run_db/somethingsomething.sqlite slurm_template.sh 1
    ```
      
      Go ahead and sbatch the bash file it just created. If everything go through, we can then do 
    ```console
    foo@bar:~/axial_run$ python2 main.py ./run_db/somethingsomething.sqlite slurm_template.sh
    ```
     You want to put this in either a `screen` or `tmux` session so the script can continuouslly submit and monitor jobs. The running database will be continuously modifiy to reflect which jobs needs to be done, so do not touch it after start running. 
    

