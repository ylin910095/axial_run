from ensemble_db import *
import hashlib, sys, random, datetime

if len(sys.argv) != 5:
    print("%s usage: db_name num_config jobid ensemble"%sys.argv[0])
    sys.exit()
db_name = sys.argv[1]
no_config = int(sys.argv[2])
jobid = sys.argv[3]
ensemble = sys.argv[4]

# Open db
db_engine = create_engine('sqlite:///' + db_name, connect_args={'timeout': 10})
Session = sessionmaker(bind=db_engine,autoflush=True, autocommit=False)
session = Session()

# Query all undone configurations
qs = session.query(Configuration).filter(Configuration.run1_status == 'Incomplete').all()
if len(qs) == 0:
    print("All done")
    sys.exit()

# Without replacement
if len(qs) > no_config:
    qs = [qs[i] for i in random.sample(range(len(qs)), k=no_config)]

# Hash the current run so we can access later
utc_datetime = datetime.datetime.utcnow()
utc_datetime = "UTC: %s"%utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
hashstr = (utc_datetime + qs[0].ensemble.name + jobid).encode("utf-8")
hashresult = hashlib.sha224(hashstr).hexdigest()
for iqs in qs:
    iqs.time_stamp = utc_datetime
    iqs.running_hash = hashresult
    iqs.run1_status = 'Running'
session.commit()

# Return array
return_list = [hashresult] + [i.configuration for i in qs]
print(" ".join(return_list))

session.close()
db_engine.dispose()
