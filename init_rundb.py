from utils.ensemble_db import *
import glob, hashlib, sys

if len(sys.argv) != 4:
    print('usage:', sys.argv[0], 'db_name', 'ensemble_name', 'config_loc')
    sys.exit(1)

(db_name, ensemble_name, config_loc) = sys.argv[1:]

# Initialize db
dbengine = create_engine('sqlite:///' + db_name)
Declare.metadata.create_all(dbengine)
Session = sessionmaker(bind=dbengine, autoflush=True, autocommit=False)
session = Session()

# First see if ensemble name exist
enint = session.query(Ensemble).filter(Ensemble.name == ensemble_name).all()
if len(enint) == 0:
    ens_inst = Ensemble(ensemble_name)
    session.add(ens_inst)
    session.commit()
else:
    ens_inst = enint[0]

ens_inst = session.query(Ensemble).filter(Ensemble.name == ensemble_name).first()
 
# Find all configurations
all_config = glob.glob(config_loc + "/*.ildg")
for ic, fn in enumerate(all_config):
    print("%s/%s"%(ic, len(all_config)))

    # Hash the gauge file with md5
    def checksumfile(filename, hash_factory=hashlib.md5, chunk_num_blocks=128):
        h = hash_factory()
        with open(filename,'rb') as f: 
            for chunk in iter(lambda: f.read(chunk_num_blocks*h.block_size), b''): 
                h.update(chunk)
        return h.hexdigest()
    checksum = checksumfile(fn) 
    """
    # Find MILC checksums
    with open(fn, errors="ignore") as openf:
        for line in openf:
            if "gauge.previous.checksums" in line:
                sl = line.split("=")
                checksum = sl[1].strip()
                break
    """
    # Parse config and series
    config_name = fn.split('/')[-1]
    series = config_name.split('-')[-2][-1]
    try:
        str(int(series)) # make sure it is not a number
        series = 'a' # default to series a
    except:
        pass
    trajectory = int(config_name.split('.')[-2])
    
    # Now dump into database
    instance = Configuration(ens_inst.id, fn, checksum, series, trajectory)
    instance.run1_status = 'Incomplete'
    session.add(instance)
    session.commit()

session.close()
dbengine.dispose()


