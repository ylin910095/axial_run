#!/bin/bash
#SBATCH --account=axialgpu-20-21
#SBATCH --nodes=8
#SBATCH --ntasks-per-node=4
##SBATCH -C pascal
#SBATCH --time=6:00:00
##SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:4
#SBATCH --partition=long
#SBATCH --job-name=g5z
#SBATCH --mail-user=99liny@gmail.com
#SBATCH --mail-type=FAIL,TIME_LIMIT
#SBATCH --qos=normal
#SBATCH --output=/sdcc/u/ylin/lqcd/yin/data/a012_physical/slurmout/g5z_t0_%j.out

no_config=1 # number of configurations per job
mpi_rank_per_node=4
openmp_thread_per_rank=8
num_nodes=$SLURM_JOB_NUM_NODES
num_nodes_per_config=$(( $num_nodes / $no_config ))
mpi_rank_per_config=$(( $num_nodes_per_config * $mpi_rank_per_node ))
ensemble=l4864f211b600m001907m05252m6382
export OMP_NUM_THREADS=${openmp_thread_per_rank}
export QUDA_RESOURCE_PATH=tunefile

run_db=/sdcc/u/ylin/axial/input_dir/a012_physical/rundb_a012_physical.sqlite
MILC_bin=/sdcc/u/ylin/axial/input_dir/a012_physical/ks_spectrum_hisq_gb_baryon_blind_no_sink_links_newblind


projdir=/sdcc/u/ylin/axial/input_dir/a012_physical
datadir=/hpcgpfs01/work/lqcd/axial/yin/data/a012_physical
MILCoutdir=${datadir}/out
pythonprompt=${projdir}/pmt_3pt_many_sinks.py
cobaltoutdir=${datadir}/slurmout
inpdir=${datadir}/inp
inpoutdir=${datadir}/out
corroutdir=${datadir}/corr/g5z_t0_newbin
propoutdir=${datadir}/prop
srcoutdir=${datadir}/src
jobscratchdir=/hpcgpfs01/work/lqcd/axial/yin/temp/${SLURM_JOBID}_temp_dir


echo "Start time:" $(date)
echo "Number of configurations:" $no_config
echo "SLURM_JOB_ID:" $SLURM_JOB_ID
echo "SLURM_JOB_NUM_NODES:" $SLURM_JOB_NUM_NODES
echo "num_nodes_per_config: " $num_nodes_per_config
echo "mpi_rank_per_node: " $mpi_rank_per_node
echo "mpi_rank_per_config: " $mpi_rank_per_config
echo "openmp_thread_per_rank: " $openmp_thread_per_rank


mkdir $jobscratchdir # temporary folder, volatile
gaugearray=($(python2 /sdcc/u/ylin/axial/input_dir/a012_physical/generate_config.py $run_db $no_config $SLURM_JOB_ID $ensemble))
running_hash=${gaugearray[0]}
counter=0
for igauge in "${gaugearray[@]:1}" # skip first element
do
    echo "Config: " $igauge
    # Generate input file
    inputfilename=$(python2 make_inpfile_name.py $igauge $SLURM_JOB_ID)
    inputfile=${jobscratchdir}/$inputfilename
    python2 $pythonprompt $igauge $SLURM_JOB_ID $jobscratchdir $propoutdir $srcoutdir > $inputfile

    milcoutname=$(python2 make_milcout_name.py $igauge $SLURM_JOB_ID)
    milcoutfile=${inpoutdir}/${milcoutname}
    
    mpirun -n ${mpi_rank_per_config} ${MILC_bin} < ${inputfile} >> ${milcoutfile}&
    sleep 1
    counter=$(( $counter + 1 ))
done
wait


# Validate results and cleanup
echo "Clean up..."
python db_scavenger.py $run_db $running_hash $MILC_bin $jobscratchdir $corroutdir $inpdir $SLURM_JOB_ID

# Create database
echo "Updating correlator database..."
python ${projdir}/database/create-DB-axial-2pt.py ${projdir}/database/DB_2pt_a012_physical.yaml &
python ${projdir}/database/create-DB-axial-3pt-Azonly.py ${projdir}/database/DB_3pt_a012_physical.yaml &
wait

#rm -rf ${jobscratchdir}
echo "End time:" $(date)
