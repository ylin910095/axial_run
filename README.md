### Prerequisite
- python2.7 (it is important to use 2.7 for MILCprompt for our run)
- scipy
- pyyaml
- sqlalchemy
- https://pythonhosted.org/Cheetah/ (for MILCprompts)
- maybe others? 

### Compile MILC

Clone the `feature/gb-baryon-ptsrc` branch of custom MILC at https://github.com/ylin910095/milc_baryon.git
Besides the usual MILC compilation steps (remember to set OMP = true to enable openMP!), you will need to go to the file ```./generic_ks/gb_baryon_mmap.c``` and edit the line reads ```#define GB_DIRECTORY``` to the desired scratch directory. All the memory maps wil be saved and automatically erased in this directory during the run. Once the Makefile is properly set, go to ```ks_spectrum``` and type ```make ks_spectrum_hisq_gb_baryon_blind_no_sink_links``` to produce binary.

### Running setup
Download the tarball in the email and untar it. Move the compiled binary in the previous step to this directory. First we have to do is generate a database that records all the configurations for a given ensemble. The configurations have to be gauge-fixed and follow the standard MILC naming convention. First we do,
```sh
python init_rundb.py db_name ensemble_name config_loc
```
where ```db_name``` is the output database name, ```ensemble_name``` is the ensemble name (eg, l1648f211b580m013m065m838),  and ```config_loc``` is the directory in which the configurations locate. This will generate a running database that will be used by slurm to coordinate the running.

Next, you have to edit ```run_param.yaml```. There are comments in the files and they should be self-explanatory. You may also need to edit ```slurm_template.sh``` to suit the system configuration. Perhaps the most common change I can think of is changing ```mpirun``` to ```srun```, but the template should stay mostly intact. Once these two files are edited, we can generate the slurm batch script by typing 

```sh
python init_batch.py run_param.yaml slurm_template.sh slurm_out.sh
```

which will generate a batch script name ```slurm_out.sh```. 

Finally, we need to edit the parameters in  MILCprompts, ```pmt_2pt_strange.py```. There are really only two things you need to edits in this files: the convergence criteria and the Gaussian smearing parameters. The convergence criteria can be changed in lines 307-308 (```L2``` and ```R2```), and the Gaussian smearing parameters can be changed in lines 151-152 (```r0_list```, the smearing radius in lattice units, and ```iter_list```, the iteration counts). We can set the smearing radius to be some numbers smallers the compton wavelength of the omega baryon and set iterations to be large enough (eg, if aM=0.7, I would do something like r=4.0, N=50). Try to do ```python2 pmt_2pt_strange.py``` and make sure you there are no errors in the test input script.

### Running
All you have to do is 

```sh
sbatch slurm_out.sh
```
The script will automatically grabs the incomplete configurations in the running database and do them. If all configurations are completed, the batch script will simply exit.

