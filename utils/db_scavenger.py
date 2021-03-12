import glob, sys, os, shutil, hashlib, socket
# Hack import 
parent_fp = os.path.dirname(os.path.dirname(os.path.abspath(os.path.realpath((__file__)))))
sys.path.append(parent_fp)
from run_db.ensemble_db import *

if len(sys.argv) != 8:
    print("%s usage: run_db running_hash MILC_bin jobscratchdir corroutdir inpdir jobid"%sys.argv[0])
    sys.exit()
run_db, running_hash, MILC_bin, jobscratchdir, corroutdir, inpdir, jobid = sys.argv[1:]

# Hash the MILC binary
with open(MILC_bin, 'rb') as fn:
    data = fn.read() 
    MILC_md5 = hashlib.md5(data).hexdigest()

# First validate if each configuration has finished running
db_engine = create_engine('sqlite:///' + run_db, connect_args={'timeout': 10})
Session = sessionmaker(bind=db_engine,autoflush=True, autocommit=False)
session = Session()

run_inst = session.query(Configuration).filter(Configuration.running_hash == running_hash).all()
for ist in run_inst:
    if ist.run1_status != "Running":
        print("WARNING: run1_status is %s"%ist.run1_status)
    
    # Search scratch directory to see if the jobs have produced correlators
    series = ist.series
    trajectory = str(ist.trajectory)
    tag = series + trajectory.zfill(4) 
    outcorr = glob.glob("%s/*_r%s_*.cor"%(jobscratchdir, tag))

    # No correlator files found, the jobs failed
    if len(outcorr) == 0: 
        ist.run1_status = "Incomplete" # revert the state
        ist.running_hash = ""
        session.commit()
        continue

    # Move the input file
    inplist = glob.glob("%s/*.inp"%(jobscratchdir))
    for iinp in inplist:
        shutil.copy2(iinp, inpdir)
    
    # Update databases and copy files to correct output location
    for ifile in outcorr:
        shutil.copy2(ifile, corroutdir) 
    ist.run1_status = "Complete"
    ist.run1_binary_md5 = MILC_md5
    ist.run1_hostname = socket.gethostname() 
    ist.run1_jobid = jobid
    with open(inpfile, 'r') as inpf:
        inpread = inpf.read()
    ist.run1_script = inpread
    session.commit()

# Clean up
session.close()
db_engine.dispose()

