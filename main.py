import yaml, sys, hashlib, datetime, copy, random, string, subprocess, time
from run_db.ensemble_db import * # all sqlalchemy imports here
from utils import gauge_utils

if len(sys.argv) != 3 and len(sys.argv) != 4:
    print('%s usage:'%sys.argv[0], 'db_name', 'slurm_template', '[debug]')
    sys.exit(1)
run_db = sys.argv[1]
slurm_template = sys.argv[2]
try:
    debug = int(sys.argv[3])
except:
    debug = 0

wait_time = 60 # Seconds to wait until next submission

while True:
    # Open db
    db_engine = create_engine('sqlite:///' + run_db, connect_args={'timeout': 10})
    Session = sessionmaker(bind=db_engine,autoflush=True, autocommit=False)
    session = Session()

    # Query all undone configurations
    qs = session.query(Configuration).join(Ensemble).join(PromptParam).filter(
                       Configuration.run1_status == 'Incomplete').all()
    if len(qs) == 0:
        print("All done")
        sys.exit(0)
    print("Numbers to do :%s"%len(qs))
    qs = qs[0]

    # Sleep for 360 seconds if max job number reached
    max_jobs = int(qs.ensemble.max_jobs)
    check_jobs_command = qs.ensemble.check_jobs_command
    jobq = int(subprocess.check_output(check_jobs_command, shell=True))
    if jobq >= max_jobs:
        wait_time = 360
        print('Maximum jobs numbers %s reached, sleep for %s seconds'%(max_jobs, wait_time))
        session.close()
        db_engine.dispose()
        time.sleep(wait_time)
        continue

    # Job bundling with the same cluster param and pmt param
    qs_id_list = []
    cluster_param = yaml.load(qs.ensemble.cluster_param)
    no_config = cluster_param['no_config']
    ensemble_id = qs.ensemble.id
    pmt_param_id = qs.pmt_param.id
    pmt_file = qs.pmt_param.pmt_file
    qs_candidate = session.query(Configuration).join(Ensemble).join(PromptParam).filter(
                                Ensemble.id == qs.ensemble.id, 
                                PromptParam.id == pmt_param_id,
                                Configuration.run1_status == 'Incomplete').limit(no_config).all()
    qs_id_todo = [i.id for i in qs_candidate]

    # Check number of jobs in queue

    # For input and output file names. This will be appended with SLURM_JOB_ID in the actual run
    def _make_sub_strs(qsin):
        run_list = []
        for iqs in qsin:
            gauge_loc = iqs.configuration
            gauge_dict = gauge_utils.parse_gauge(gauge_loc)
            series_trajc = gauge_dict['series'] + str(gauge_dict['trajectory']).zfill(4)
            run_name = '%s_rundbid_%s_%s'%(iqs.pmt_param.name_tag, 
                                           iqs.id, series_trajc)
            run_list.append(run_name)
            # We will dump pmt str content to a temporary file

        run_str = " ".join(run_list)
        return run_str
    run_str = _make_sub_strs(qs_candidate) 
    qs_id_str = " ".join([str(i) for i in qs_id_todo])

    # Hash the current run so db_scavenger can access them later to clean up
    utc_datetime = datetime.datetime.utcnow()
    utc_datetime = "UTC: %s"%utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
    N = 10
    random_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))
    hashstr = (utc_datetime + random_str).encode("utf-8")
    hashresult = hashlib.sha224(hashstr).hexdigest()

    # Reconstruct substitute dictionary
    substitute_param = copy.deepcopy(cluster_param)
    substitute_param['slurm_header'].append(
        "#SBATCH --output=%s/slurmout/%s_slurm_%%j_runid_%s.slurmout"%(
                                               substitute_param['datadir'],
                                               qs_candidate[0].pmt_param.name_tag,
                                               "_".join([str(i) for i in qs_id_todo]))
    )
    substitute_param['slurm_header'] = "\n".join(substitute_param['slurm_header'])
    substitute_param['module_command'] = "\n".join(substitute_param['module_command'])
    substitute_param['running_hash'] = hashresult
    substitute_param['file_name_list'] = run_str
    substitute_param['rundb_id_list'] = qs_id_str
    substitute_param['pythonprompt'] = pmt_file
 
    # TODO: restrict which variables can be substituted
    with open(slurm_template, 'r') as st:
        s = string.Template(st.read())
        ns = s.safe_substitute(**substitute_param)

    # Save batch file to be executed. Reuse if the same file already exists.
    bash_fn = "%s.sh"%hashresult # temporary filename, it will change once we got jobid
    bash_dir = substitute_param['datadir'] + '/bash/' # make sure the folder exist
    bash_loc = bash_dir + bash_fn
    slurmout = 'test.txt'
    with open(bash_dir+bash_fn, 'w') as so:
        so.write(ns)

    # Submit job
    if debug:
        jobid = 'debug'
    else:
        jobout = subprocess.check_output('sbatch %s'%bash_loc, shell=True)
        jobid = jobout.decode('utf-8').split()[-1]
        print("Submit %s"%jobid)
    new_bash_fn = "%s_slurm_%s_runid_%s.sh"%(qs_candidate[0].pmt_param.name_tag, jobid, 
                                          "_".join([str(i) for i in qs_id_todo]))
    os.rename(bash_loc, bash_dir+new_bash_fn)

    # Update rundb after submitted 
    if not debug:
        for iqs in qs_candidate:
            iqs.time_stamp = utc_datetime
            iqs.running_hash = hashresult
            iqs.run1_status = 'Queued'
        session.commit()

        session.close()
        db_engine.dispose()

        jobq = int(subprocess.check_output(check_jobs_command, shell=True))
        if jobq == 0:
            raise Exception('Fail to see submitted jobs')
        print('Number of jobs in queue: %s'%jobq)
        time.sleep(0.5)

    else:
        print('Debug bash file at %s'%bash_dir+new_bash_fn)
        sys.exit(0)

