import yaml, sys, sys
import numpy as np
import os.path
from MILCprompts.MILCprompts import *
from MILCprompts.calcNaikEps import *
from MILCprompts.nameFormat import *
# Hack import
parent_fp = os.path.dirname(os.path.dirname(os.path.abspath(os.path.realpath((__file__)))))
sys.path.append(parent_fp)
from run_db.ensemble_db import *

from pmt_2pt_kernel import pmt_2pt_kernel

# VERY IMPORTANT: use python2.7 or
# the tsrc location is NOT reproducible
# see https://stackoverflow.com/questions/40137072/why-is-hash-slower-under-python3-4-vs-python2-7
# essentially, str hashing uses a different algorithm from python2.7 to python3
# and hashing randomization is enabled by default in python3. Thats why tsrc is not
# reproducible anymore
if sys.version_info[0] != 2:
    import zlib
    # redefine hash function for tsrc randomization
    # notice that this is incompatible with tsrc generated from python2!!
    def hash(x):
        return zlib.adler32(bytes(str(x),encoding='utf8'))
else:
    raise Exception("Don't use python2")

## -- argument 1: gauge file location
## -- argumetn 2: jobid
## -- argument 3: output correlator
## -- argumetn 4: output propagator
## -- argument 5: output source
##    l1648f211b580m013m065m838a.200.ildg
if len(sys.argv) != 1 and len(sys.argv) != 3 and len(sys.argv) != 7:
    print("%s usage: run_db rundb_id [jobid] [outcoor] [outprop] [outsrc]"%sys.argv[0])
    sys.exit()

elif len(sys.argv) == 1:
    print("Testing")
    gaugefile = "/projects/AxialChargeStag/hisq/l6496f211b630m0012m0363m432/gauge/l6496f211b630m0012m0363m432p-Coul.315.ildg"
    jobid = '88888'
    projDir='/this_is_test_proj_Dir'
    lqcdDir=projDir
    outprop = '/test_outprop'
    outsrc = '/test/src'
    pmt_file = __file__
    pmt_param = {'t0_list': [0, 2, 4, 6], 'mass': 0.05,
                 'gauss_smearing': {'r0': 1.0, 'N': 24},
                 'inversion': {'L2': 1e-12, 'R2': 0, 'restarts': 50, 'iters': 8888} # invertor control
                 }

elif len(sys.argv) == 3:
    jobid = '88888'
    projDir='/this_is_test_proj_Dir'
    lqcdDir=projDir
    outprop = '/test_outprop'
    outsrc = '/test/src'

else:
    jobid = sys.argv[3]
    projDir = sys.argv[4]
    outprop = sys.argv[5]
    outsrc = sys.argv[6]
    lqcdDir = projDir
    
# Gauge field layout - machine and geoemtry dependent
# Set layout to None will disable this prompt completely
layout = {'node': (1, 2, 2, 2), 'io': (1, 1, 1, 2)}

# Load pmt information from database
if len(sys.argv) == 3 or len(sys.argv) == 7:
    run_db = sys.argv[1]
    rundb_id = int(sys.argv[2])
    db_engine = create_engine('sqlite:///' + run_db, connect_args={'timeout': 10})
    Session = sessionmaker(bind=db_engine,autoflush=True, autocommit=False)
    session = Session()
    qs = session.query(Configuration).join(PromptParam).filter(Configuration.id==rundb_id).first()
    gaugefile = qs.configuration
    pmt_param = yaml.load(qs.pmt_param.param_dict)
    pmt_file = qs.pmt_param.pmt_file
    session.close()
    db_engine.dispose()

# Check to make sure we are using the right pmt file for this param
fullpath = os.path.dirname(os.path.abspath(os.path.realpath((__file__)))) +\
            '/' + os.path.basename(__file__)
if not fullpath == os.path.abspath(os.path.realpath(pmt_file)):
    raise Exception('Incomptaible prompt file and parameters')
jobid = str(jobid.split('.')[0])

# Smearing controls and tags
gparam_list = []
r0_list = [pmt_param['gauss_smearing']['r0'],]
iter_list = [pmt_param['gauss_smearing']['N'],]
for i in range(len(r0_list)):
    tmp_gparam = {
                  'type': 'gaussian',
                  'stride': 2,
                  'r0': r0_list[i],
                  'iters': iter_list[i],
                  }
    gparam_list.append(tmp_gparam)

# Add tags
for i in range(len(gparam_list)):
    paramdict = gparam_list[i]
    if paramdict['type'] == "gaussian":
        pfsmear = "G"
    elif paramdict['type'] == "laplacian":
        pfsmear = "L"
    else:
        raise
    (gparam_list[i])['tag'] = "%sr%.1fN%s" %(pfsmear, paramdict['r0'], paramdict['iters'])

spect = None
for current_t0 in pmt_param['t0_list']:
  # Wall sources - set1 from freshly loaded configs
  set1_srcsnk_dict = {
    # Source
    'srcTimeslices': (current_t0, ),
    'srcTypeList': ('wall', ),
    'srcBaseList': (None, ),
    'srcDoLoad': (False, ),
    'srcDoSave': (False, ),
    'srcSolve': (True, ), 
    'srcSmearingParam': (None, ),
    'srcLabelOverride': (None, ),
    'srcTagMomenta': ('00', ),
    # Quark
    'basePropList': (0, 0), 
    'quarkTypeList': ("identity", "gauss"),
    'quarkBaseList': (None, None), 
    'quarkSmearParam': (None, gparam_list[0]), # only use the first smearing param
    'quarkLabelOverride': (None, gparam_list[0]['tag']),
    'quarkSinkTypeList': ("point", "point"),
  }

  # Smeared sources - continued from set1
  set2_srcsnk_dict = {
    # Source
    'srcTimeslices': (current_t0,)*3, 
    'srcTypeList': ("point", "xport", "gauss"),
    'srcBaseList': (None, 0, 1),
    'srcDoLoad': (False, )*3,
    'srcDoSave': (False, )*3,
    'srcSolve': (False, False, True), 
    'srcSmearingParam': (None, None, gparam_list[0]), # only use the first smearing param
    'srcLabelOverride': (None, None, gparam_list[0]['tag']),
    'srcTagMomenta': ('00', '00', '00'),
    # Quark
    'basePropList': (0, 0), 
    'quarkTypeList': ("identity", "gauss"),
    'quarkBaseList': (None, None), 
    'quarkSmearParam': (None, gparam_list[0]), # only use the first smearing param
    'quarkLabelOverride': (None, gparam_list[0]['tag']),
    'quarkSinkTypeList': ("point", "point"),
  }

  all_srcsnk_dict = [set1_srcsnk_dict, set2_srcsnk_dict]
    
  base_param_dict = {
      # pmt params
      'pmt_param': pmt_param,
      'projDir': projDir,
      'jobid': jobid,
      'outprop': outprop,
      # Gauge file
      'gaugefile': gaugefile,
      'layout': layout,
  }
  for srcsnk_dict in all_srcsnk_dict:
      param_dict = {'spect': spect, **base_param_dict, **srcsnk_dict}
      spect = pmt_2pt_kernel(**param_dict)
spect.generate()

if len(sys.argv) == 1 or len(sys.argv) == 3:
    print('================= end of test output ==================')
    print('')
    print('Prompt input param:')
    for key, val in list(pmt_param.items()):
        print(key, val)
