from ensemble_db import *
import glob, os, hashlib, sys, yaml
# Hack import 
parent_fp = os.path.dirname(os.path.dirname(os.path.abspath(os.path.realpath((__file__)))))
sys.path.append(parent_fp)
from utils import gauge_utils

if len(sys.argv) != 4:
    print("%s usage: db_name run_param_yaml gauge_checksum"%sys.argv[0])
    sys.exit(0)

# Read inputs
db_name = str(sys.argv[1])
with open(sys.argv[2], 'r') as yf:
    run_dict = yaml.load(yf, yaml.FullLoader)
if int(sys.argv[-1]):
    gauge_checksum = True
else:
    gauge_checksum = False

# Initialize db
dbengine = create_engine('sqlite:///' + db_name)
Declare.metadata.create_all(dbengine)
Session = sessionmaker(bind=dbengine, autoflush=True, autocommit=False)
session = Session()

# First see if ensemble names exist
for ensemble_name in run_dict:
    cluster_param = yaml.dump(run_dict[ensemble_name]['cluster_param'])
    max_jobs = run_dict[ensemble_name]['max_jobs']
    check_jobs_command = run_dict[ensemble_name]['check_jobs_command']
    enint = session.query(Ensemble).filter(Ensemble.name == ensemble_name,
                                           Ensemble.max_jobs == max_jobs,
                                           Ensemble.check_jobs_command == check_jobs_command,
                                           Ensemble.cluster_param == cluster_param).all()
    if len(enint) == 0:
        ens_inst = Ensemble(ensemble_name, max_jobs, check_jobs_command, cluster_param)
        session.add(ens_inst)
        session.commit()
    ens_inst = session.query(Ensemble).filter(Ensemble.name == ensemble_name,
                                              Ensemble.max_jobs == max_jobs,
                                              Ensemble.check_jobs_command == check_jobs_command,
                                              Ensemble.cluster_param == cluster_param).first()

    # Find all configurations
    config_loc = run_dict[ensemble_name]['loc']
    pmt_file = run_dict[ensemble_name]['pmt_file']
    all_config = glob.glob(config_loc + "/*.ildg") # assume gauge fixed configs

    for name_tag, pmt_param in run_dict[ensemble_name]["pmt_param"].items():
        dump_param = yaml.dump(pmt_param)

        # First find if pmt param is already in 
        pmtqs = session.query(PromptParam).filter(PromptParam.pmt_file == pmt_file,
                                                  PromptParam.param_dict == dump_param).all()
        if len(pmtqs) == 0:
            cpmtqs = PromptParam(pmt_file, dump_param, name_tag)
            session.add(cpmtqs)
            session.commit()
        pmtqs = session.query(PromptParam).filter(
            PromptParam.pmt_file == os.path.abspath(os.path.realpath(pmt_file)),
            PromptParam.name_tag == name_tag,
            PromptParam.param_dict == dump_param).first()

        # Skip the ones that are already in the database
        undone_config = []
        for iconfig in all_config:
            if len(session.query(Configuration).filter(
                   Configuration.configuration == os.path.abspath(
                       os.path.realpath(iconfig)), # config in ensemble is always in abs and real pahts
                   Configuration.pmt_param_id == pmtqs.id).all()) == 0:
                undone_config.append(iconfig)
            
        for ic, fn in enumerate(undone_config):
            print("%s: %s"%(fn, name_tag))
            print("%s/%s"%(ic+len(all_config)-len(undone_config), len(all_config)))
        
            # Hash the gauge file with md5 if requested
            if gauge_checksum:
                def checksumfile(filename, hash_factory=hashlib.md5, chunk_num_blocks=128):
                    h = hash_factory()
                    with open(filename,'rb') as f: 
                        for chunk in iter(lambda: f.read(chunk_num_blocks*h.block_size), b''): 
                            h.update(chunk)
                    return h.hexdigest()
                checksum = checksumfile(fn) 
            else:
                checksum = "nan"

            # Parse config and series
            gauge_dict = gauge_utils.parse_gauge(fn)
            series = gauge_dict['series']
            trajectory = gauge_dict['trajectory']

            # Now dump into database
            instance = Configuration(ens_inst.id, pmtqs.id,
                                     fn, checksum, series, trajectory)
            instance.run1_status = 'Incomplete'
            session.add(instance)
        session.commit()

session.close()
dbengine.dispose()

print("All initialized.")
