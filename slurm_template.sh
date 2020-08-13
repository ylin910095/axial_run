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
ensemble=${ensemble}
export OMP_NUM_THREADS=${openmp_thread_per_rank}
export QUDA_RESOURCE_PATH=${QUDA_RESOURCE_PATH}

projdir=${projdir}
datadir=${datadir}

run_db=${projdir}/${rundb}
MILC_bin=${projdir}/${milcbin}


MILCoutdir=${datadir}/out
pythonprompt=${projdir}/${pythonpromt}
cobaltoutdir=${datadir}/slurmout
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
gaugearray=($(python2 ${projdir}/utils/generate_config.py $run_db $no_config $SLURM_JOB_ID $ensemble))
running_hash=${gaugearray[0]}

# For job cleanup when finished or timeout. It will
# move update the running database and moving the correlators
# to the output location
dbcleanup()
{
    echo "Timout! dbcleaup() called at $(date)"
    python ${projdir}/utils/db_scavenger.py $run_db $running_hash $MILC_bin $jobscratchdir $corroutdir $inpdir $SLURM_JOB_ID
}

counter=0
for igauge in "${gaugearray[@]:1}" # skip first element
do
    echo "Config: " $igauge
    # Generate input file
    inputfilename=$(python2 ${projdir}/utils/make_inpfile_name.py $igauge $SLURM_JOB_ID)
    inputfile=${jobscratchdir}/$inputfilename
    python2 $pythonprompt $igauge $SLURM_JOB_ID $jobscratchdir $propoutdir $srcoutdir > $inputfile

    milcoutname=$(python2 ${projdir}/utils/make_milcout_name.py $igauge $SLURM_JOB_ID)
    milcoutfile=${inpoutdir}/${milcoutname}
    
    # Change this line to srun if necessary
    mpirun -n ${mpi_rank_per_config} ${MILC_bin} < ${inputfile} >> ${milcoutfile}&

    sleep 1
    counter=$(( $counter + 1 ))
done

trap 'dbcleanup' USR1 # call cleanup function when timeout
wait


# Validate results and cleanup
echo "Clean up..."
python ${projdir}/utils/db_scavenger.py $run_db $running_hash $MILC_bin $jobscratchdir $corroutdir $inpdir $SLURM_JOB_ID

#rm -rf ${jobscratchdir}
echo "End time:" $(date)
