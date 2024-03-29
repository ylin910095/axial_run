#!/bin/bash
# Asks SLURM to send the USR1 signal 60 seconds before end of the time limit
#SBATCH --signal=B:USR1@60
${slurm_header}

# Module loading
${module_command}

no_config=${no_config} # number of configurations per job
mpi_rank_per_node=${mpi_rank_per_node}
openmp_thread_per_rank=${openmp_thread_per_rank}
num_nodes=$SLURM_JOB_NUM_NODES
num_nodes_per_config=$(( $num_nodes / $no_config ))
mpi_rank_per_config=$(( $num_nodes_per_config * $mpi_rank_per_node ))
export OMP_NUM_THREADS=${openmp_thread_per_rank}
export QUDA_RESOURCE_PATH=${QUDA_RESOURCE_PATH} # only used for GPU runnings

# Directory structure
projdir=${projdir}
datadir=${datadir}

run_db=${projdir}/run_db/${rundb}
MILC_bin=${projdir}/bin/${milcbin}

MILCoutdir=${datadir}/out
pythonpromptdir=${pythonprompt}
inpdir=${datadir}/inp
inpoutdir=${datadir}/out
corroutdir=${datadir}/corr
propoutdir=${datadir}/prop
srcoutdir=${datadir}/src
jobscratchdir=${scratchdir}/${SLURM_JOBID}_temp_dir

echo "Start time:" $(date)
echo "Number of configurations:" $no_config
echo "SLURM_JOB_ID:" $SLURM_JOB_ID
echo "SLURM_JOB_NUM_NODES:" $SLURM_JOB_NUM_NODES
echo "num_nodes_per_config: " $num_nodes_per_config
echo "mpi_rank_per_node: " $mpi_rank_per_node
echo "mpi_rank_per_config: " $mpi_rank_per_config
echo "openmp_thread_per_rank: " $openmp_thread_per_rank

mkdir $jobscratchdir # temporary folder, volatile

rundb_id_list=(${rundb_id_list}) # sub from main.py. Bash array.
running_hash=${running_hash} # sub from main.py
file_name_list=(${file_name_list}) # sub from main.py. Bash array.

# For job cleanup when finished or timeout. It will
# move update the running database and moving the correlators
# to the output location
dbcleanup()
{
    echo "Timout! dbcleaup() called at $(date)"
    python2 ${projdir}/utils/db_scavenger.py $run_db $running_hash $MILC_bin $jobscratchdir $corroutdir $inpdir $SLURM_JOB_ID
}

count=0
for rundb_id in ${rundb_id_list[@]} 
do
    ifile_name=${file_name_list[count]}
    echo "Run param: " $ifile_name

    # Generate input files
    inputfilename="${ifile_name}_${SLURM_JOB_ID}.inp"
    inputfile=${jobscratchdir}/$inputfilename
    python2 $pythonpromptdir $run_db $rundb_id $SLURM_JOB_ID $jobscratchdir $propoutdir $srcoutdir > $inputfile

    # Generate output file name
    milcoutname="${ifile_name}_${SLURM_JOB_ID}.out"
    milcoutfile=${inpoutdir}/${milcoutname}
    
    # Actual work. Change this line to srun if necessary
    mpirun -n ${mpi_rank_per_config} ${MILC_bin} < ${inputfile} >> ${milcoutfile}&

    # Update database status. Timeout after 10 second to avoid DB locks.
    sqlite3 -cmd ".timeout 10000" $run_db "update configuration set run1_status='Running' where id==${rundb_id}"

    sleep 1
    count=$((count+1))
done

trap 'dbcleanup' USR1 # call cleanup function when timeout
wait

# Validate results and cleanup. This assume a job is successful
# when there are correlators file ends with ".cor" produced at 
# the scratch directory. Otherwise, it will revert the run_status
# to Incompelte.
echo "Clean up..."
python2 ${projdir}/utils/db_scavenger.py $run_db $running_hash $MILC_bin $jobscratchdir $corroutdir $inpdir $SLURM_JOB_ID

rm -rf ${jobscratchdir} 
echo "End time:" $(date)
