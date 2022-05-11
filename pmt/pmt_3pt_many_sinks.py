import yaml,sys,random
import numpy as np
import os.path
import random
import string
import math
from MILCprompts.MILCprompts import *
from MILCprompts.calcNaikEps import *
from MILCprompts.nameFormat import *
import sys
#from copy import deepcopy
from run_db.ensemble_db import *

# VERY IMPORTANT: use python2.7 or 
# the tsrc location is NOT reproducible
# see https://stackoverflow.com/questions/40137072/why-is-hash-slower-under-python3-4-vs-python2-7
# essentially, str hashing uses a different algorithm from python2.7 to python3
# and hashing randomization is enabled by default in python3. Thats why tsrc is not
# reproducible anymore
if sys.version_info[0] != 2:
    raise Exception("Python 2 is required or tsrc is not reproducible!!!!")

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
  pmt_param = {'t0': 0,
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
  
gconf = (gaugefile.split("/")[-1]).split("-")[0]
try:
    str(int(gconf[-1]))
except:
    gconf = gconf[:-1]
trajc = gaugefile.split(".")[-2]
gcset = gaugefile.split("-")[-2][-1]
jobid = str(jobid.split('.')[0])

try:
  str(int(gcset))
  gcset = "a" # default silent set a
except:
  pass

tmass = [float('0.'+gconf.split('m')[i]) for i in range(1,3)]
smass = [gconf.split('m')[i] for i in range(1,3)]
dim = [gconf.split('f')[0][1:3],gconf.split('f')[0][1:3],
        gconf.split('f')[0][1:3],gconf.split('f')[0][3:]]

## TODO: fix u0
gbet = int(gconf.split('b')[1][0:3])
if   gbet == 580:
  lattA = 0.15
  u0 = 0.855350
elif gbet == 600:
  lattA = 0.12
  u0 = 0.855350
elif gbet == 630:
  lattA = 0.09
  u0 = 0.855350
elif gbet == 672:
  lattA = 0.06
  u0 = 0.855350
#l96192f211b672m0008m022m260

## -- if a source/propagator is missing when loaded, generate a new one instead of terminating
##    save the newly generated object to the place where it was looking for it before
generateMissing = True

## -- if reloading a cw source, do the 2-point baryon/meson tie-ups again
generateNewCorr = True

## -- approximately randomize over tstart, want something reproduceable
series = 0
def prn_timeslice(traj,series,dim):
  return hash(hash(str(traj)+str(series)+"x")) % dim
s_size=int(dim[0])
t_size=int(dim[3])
## -- prn sometimes gets stuck in infinite loop
##    altering with rnchg gets out of loop
##    constructed in a way to prevent breaking those that did work after few iters
rniter = 0
rnchg = ''
tstart = -1
while (tstart % 2 == 1):
  tstart = prn_timeslice(str(int(trajc)+max(tstart,0))+rnchg,series,t_size)
  rniter += 1
  if rniter % 10 == 9:
    rnchg = rnchg + str(tstart)
#tstart=0

## stupid fn to randomize cube index over tsrc,tins,trajectory,series and solve number
## make sure subsequent solves always give different cube indices
def prn_cube(tsrc,tins,traj,series,num):
  if num > 8:
    raise IndexError("only 8 cube sites allowed; all used")
  x = str(hash(hash(str(tsrc)+'y'+str(tins)+'z'+str(traj)+'t'+str(series)+'x')))[2:]
  t = list(range(8))
  it = 0
  c = -1
  for it in range(num+1):
    c += 1
    if c == len(x):
      x = str(hash(x))[2:]
      c = 0
    while int(x[c]) > len(t)-1:
      c += 1
      if c == len(x):
        x = str(hash(x))[2:]
        c = 0
    rval = t.pop(int(x[c]))
  return rval
timeBC = "antiperiodic"

# g5z done so far on lq: src = 0, 16, 32, 48
# g5z assignment lq: 8, 40
# g5z assignment bnl ic: 24, 56

srcTimeslices = (pmt_param["t0"],) # the last two are dummy for tieups 
srcDoLoad = (False, False, False, False) 
srcDoSave = (False, False)
snkDoLoad = (False, False) #do NOT load and save at same time!
snkDoSave = (False, False)
srcSolve = (True, True) # do we want to solve this set of propagators? It is 
                         # useful we only want to use it as base source to have modified 
                         # sources but we do not want to solve for the base sources.


## TODO: make sure doMomenta updated to doSrcMomenta
doSrcMomenta = False
srcGenMomenta = ((0,0,0),(0,0,0)) # momentum on source inversions
srcTagMomenta = ('00','00') # tag for momentum on source
srcZeroMomenta = (0,0) # index of base source to use

stride = 2 
r0_fm = 0.9 
N0 = 3 

# Smearing controls, if type == "laplacian", only stride param will be used;
# if type == "gaussian:, stride, r0, and iters will be used

gparam_list = []
r0_list = [3, ]
#r0_list = [2, 6]
iter_list = [40, ]
#iter_list = [30, 70]
for i in range(len(r0_list)):
    tmp_gparam = {
                  'type': 'gaussian',
                  'stride': stride,
                  'r0': r0_list[i],
                  'iters': iter_list[i],
                  }
    gparam_list.append(tmp_gparam)

# Add tag to identify 
for i in range(len(gparam_list)):
    paramdict = gparam_list[i]
    if paramdict['type'] == "gaussian":
        pfsmear = "G"
    elif paramdict['type'] == "laplacian":
        pfsmear = "L"
    else:
        raise
    (gparam_list[i])['tag'] = "%sr%.1fN%s" %(pfsmear, paramdict['r0'], paramdict['iters'])

srcSmearing = (False, True, ) # to smear or not to smear
srcSmearingBaseSrc = (None, 0, ) # if do smearing, which source to derive it from
srcSmearingParam = (None, )
srcSmearTag = ("", "",) # NOT USED! Eliminate later!

## Sink controls
snkSrc = (0, 0, 0, 0) # which source octet does the sink octet belongs to. Only count those that are solved!
snkSmearingParam = tuple(gparam_list)
snkSmearTag = ("", ) # NOT USED! Eliminate later.

## parameters to make insertions with
insTimeSep = (7,8,9,10)
insCurrent = ((0,0),(11,11),)  
insMomenta = ((0,0,0),(0,0,0)) # sequential momentum inversions
insTagMomenta = ('00','00') # tag for momentum

# STEP BY STEP INPUT GUIDE!
# FOLLOW THIS! OR YOU WILL MAKE MISTAKES!
# 1. Change insQuartet 
# 2. Change insSrcIndex
# 3. Chnage insDoProject
# 4. Change currTie
# 5. Check consistency between all entries above
# 6. Check python pmt output
# 7. SUBMIT!
## 4-tuples of (timesource,timesep,current,momenta) indices
insQuartet = ((0,0,1,1), (0,1,1,1), (0,2,1,1),(0,3,1,1)) #set1 done PROJECT IT
#insQuartet = ((0,0,1,1),)
#insQuartet = ()
insSrcDoSave = tuple(True for x in insQuartet) # whetever to save extend quark at sink

## decoupled from other source objects
insSrcIndex = (0,1,2,3,4,5)
insDoLoad = tuple(False for x in insSrcIndex)
insDoSave = tuple(True for x in insDoLoad)

insDoProject = (False,False,False,False,False,False)
cornerIter = 0 ## number 0-7, higher numbers choose different corners
insProjectIndex = tuple(cornerIter for x in insSrcIndex)

## specific tie-ups for specific currents
currTieScalar = ((0, 0), )
currTieAz = ((11,11),)
currTieV4 = ((8, 8),)
currTieV4VX4 = ((8, 9),)
currTieG5XG5 = ((14, 15),)
currTieAx = ((14,14),)
currTieG5XGXT = ((14, 9),)
currTieG5XG5 = ((14,15),)
currTieGTG5 = ((8, 15),)
currTieG5XG5Y = ((14, 13), )
currTieG45G45 = ((7, 7), )
currTieG4G5X = ((8, 14),)
currTieAll = ((7,7),(14,14),(13,13),(11,11),(8,8),(1,1),(2,2),(4,4))
#currTie = (currTieAll,currTieAll,currTieAz,currTieAz)
#currTie = (currTieV4, currTieV4)
#currTie = (currTieAll,currTieAz)
currTie = [currTieAz]*len(insQuartet)
do2pt = True
doMeson2pt = False
doCWMeson2pt = True
    
rndSeries = 'rnd0series'

#numRandomSnk = 1
#randomSnkKeys = ['rnd0','rnd1','rnd2','rnd3'][:numRandomSnk]
#if numRandomSnk > len(randomSnkKeys):
#  raise ValueError # not enough sink keys!

tagString = '01.'
def specFile2ptMesonPrefix():
  return projDir+'/mes2pt.'+tagString
def specFile2ptBaryonPrefix():
  return projDir+'/bar2pt.'+tagString
## TODO: fix for new 3-point functions
def specFile3ptBaryonPrefix():
  return projDir+'/bar3pt.'+tagString
def specFileMidfix():
  return 'l'+str(dim[0])+str(dim[3])\
   +'_r'+gcset+trajc.zfill(4)\
   +NameFormatMass('_m$m',tmass[0])
def specFilePostfix():
  return 'c'+jobid+'.coul.cor'

gammalabel=['G1','GX','GY','GXY','GZ','GZX','GYZ','G5T',
            'GT','GXT','GYT','G5Z','GZT','G5Y','G5X','G5']
def gen_label(gs,gt):
  if gs == 127 or gt == 127:
   return "2point"
  return gammalabel[gs]+'-'+gammalabel[gt]
def gen_norm(gs,gt,rN):
  return (1,'*',rN)
def val_to_hex(g):
  if g == 127:
   gx = 0
  else:
   gx = g
  return str([0,1,2,3,4,5,6,7,8,9,'A','B','C','D','E','F'][gx])
def gen_hex(gs,gt):
 return val_to_hex(gs)+val_to_hex(gt)

# lattice stuff
sciDAC = None # { 'node': [ 4, 4, 4, 8 ], 'io': [ 4, 4, 4, 8 ] }
prompt = 0
wkflName = 'workflow-test-brw'
## putting numbers at end doesn't change seed by much
spect = ks_spectrum(wkflName,dim,np.abs(hash(rndSeries)),'job-test-baryon-ks-spectrum',sciDAC,prompt)


# Default gauge config location on IC BNL
uLoad = ('reload_parallel', gaugefile)

#gFix = 'coulomb_gauge_fix'
gFix = 'no_gauge_fix' # already gauge fixed, don't change
gStr = 'coul'
uSave = ('forget', )
fatLink = { 'weight': 0, 'iter': 0 }
Uorigin = [0,0,0,0]
spect.newGauge(Gauge(uLoad,u0,gFix,uSave,fatLink,Uorigin,timeBC))

## to reuse same configuration -> save memory for orthogonal runs!
#spect.newGauge(Gauge(('continue',),u0,gFix,uSave,fatLink,Uorigin))
## turn on 3-point functionality!
spect.GB3PointOn()

## CORNER WALLS - first time through

## base corner wall sources
subset = 'full'
scaleFactor = None
save = ('forget_source',)
srcPSoct = list()

"""
for i,(tsrc,idx,mom,tag) in enumerate(zip(
    srcTimeslices,srcZeroMomenta,srcGenMomenta,srcTagMomenta)):
  #label = 'cc$it'+str((tstart+tsrc)%t_size)
  if doSrcMomenta:
   label = 'p'+str(tag)+'c$i'+str((tstart+tsrc)%t_size)
  else:
   label = 'cw$i'
  if (idx == i) or not(doSrcMomenta):
   ## do zero momentum as base source!
   srcPSoct.append(CornerWall8Container(
    str((tstart+tsrc)%t_size),subset,scaleFactor,label,save))
   srcPSoct[-1].addSourcesToSpectrum(spect)
   spect.addSourceOctet(srcPSoct[-1])
  else:
   ## use zero momentum base source to generate momentum corner wall!
   def momFunc(src8,label,save):
    return MomentumModSource(src8,mom,label,save)
   srcPSoct.append(GeneralSource8Modification(srcPSoct[idx],momFunc,label,save))
   srcPSoct[-1].addSourcesToSpectrum(spect)
   spect.addSourceOctet(srcPSoct[-1])
"""
for i,(tsrc,idx,mom,tag,doSmear) in enumerate(zip(
    srcTimeslices,srcZeroMomenta,srcGenMomenta,srcTagMomenta,srcSmearing)):
    #label = 'cc$it'+str((tstart+tsrc)%t_size)
    if doSrcMomenta and doSmear:
        raise ValueError("Scipt does not support non-zero momenta with smearing!")
    if doSrcMomenta:
        label = 'p'+str(tag)+'c$i'+str((tstart+tsrc)%t_size)
    elif doSmear:
        label = 'cw$i%s'%(srcSmearingParam[i])['tag']
    else:
        label = 'cw$i'
    if (idx == i) or (not(doSrcMomenta) and not(doSmear)):
        ## do zero momentum as base source!
        srcPSoct.append(CornerWall8Container(
         str((tstart+tsrc)%t_size),subset,scaleFactor,label,save))
        srcPSoct[-1].addSourcesToSpectrum(spect)
        spect.addSourceOctet(srcPSoct[-1])
    elif doSmear: # gaussian smearing source
        def smearFunc(src8,label,save):
            if (srcSmearingParam[i])["type"]  == "gaussian":
                return FatCovariantGaussian(srcSmearingParam[i], label, save, src8)
            if (srcSmearingParam[i])["type"] == "laplacian":
                return FatCovariantLaplacian((srcSmearingParam[i])["stride"], label, save, src8)
        srcPSoct.append(GeneralSource8Modification(srcPSoct[idx],smearFunc,label,save))
        srcPSoct[-1].addSourcesToSpectrum(spect)
        spect.addSourceOctet(srcPSoct[-1])
    else: # non-zero momenta source
        ## use zero momentum base source to generate momentum corner wall!
        def momFunc(src8,label,save):
            return MomentumModSource(src8,mom,label,save)
        srcPSoct.append(GeneralSource8Modification(srcPSoct[idx],momFunc,label,save))
        srcPSoct[-1].addSourcesToSpectrum(spect)
        spect.addSourceOctet(srcPSoct[-1])



## inversion parameters
momTwist = (0,0,0)
#CGparam = { 'restarts': 5, 'iters': 500 }
#CGparam = { 'restarts': 15, 'iters': 1000 } ## l3248
CGparam = { 'restarts': 300, 'iters': 8000 } ## l4864 ## TODO: have gconf dependent solution?
CGparamLoad = CGparam ## -- shouldn't matter, safe option
solvePrecision = 2
masses = [ tmass[0] ] ## always physical
naik = list(calcNaikEps(np.array(masses)*lattA))
naik = (0,0)
residuals = { 'L2': 1e-10, 'R2':0}

## corner wall solves
invPSoct = list()
def cwmomsave(tsrc,mom,doSave):
  if mom == '00':
   momstr = ''
  else:
   momstr = '_p'+mom
  if doSave:
    return (
      'save_ascii_ksprop',
      outprop\
      +'/l'+str(dim[0])+str(dim[3])\
      +'_r'+trajc.zfill(4)+gcset\
      +'_m$m'\
      +'_cwsc'\
      +'_t'+str((tstart+tsrc)%t_size)\
      +'_$i'\
      +momstr\
      +'_'+gStr+'.prop' )
  else:
    return ('forget_ksprop',)
  pass
"""
for tsrc,src,doLoad,doSave,tag in zip(srcTimeslices,srcPSoct,srcDoLoad,srcDoSave,srcTagMomenta):
  if doLoad:
    check = 'yes'
    load = ('reload_parallel_ksprop',cwmomsave(tsrc,tag,True)[1])
    invPSoct.append(KSsolveSet8Container(
      src,momTwist,timeBC,check,CGparamLoad,solvePrecision,
      masses,naik,load,cwmomsave(tsrc,tag,doSave),residuals))
  else:
    check = 'yes'
    load = ('fresh_ksprop',)
    invPSoct.append(KSsolveSet8Container(
      src,momTwist,timeBC,check,CGparam,solvePrecision,
      masses,naik,load,cwmomsave(tsrc,tag,doSave),residuals))
  ## -- safeguard against missing
  if generateMissing and doLoad:
    for ss in invPSoct[-1].solveset:
      for prop in ss.propagator:
        if not(os.path.exists(prop.load[1])):
          ss.check = 'yes'
          prop.save = ('save_serial_scidac_ksprop',
            prop.load[1])
          prop.load = ('fresh_ksprop',)
  invPSoct[-1].addSolvesToSpectrum(spect)
"""
for tsrc,src,doLoad,doSave, doSolve, tag in zip(srcTimeslices,srcPSoct,srcDoLoad,srcDoSave,srcSolve,srcTagMomenta):
    if not doSolve:
        continue
    if doLoad:
        check = 'yes'
        load = ('reload_parallel_ksprop',cwmomsave(tsrc,tag,True)[1])
        invPSoct.append(KSsolveSet8Container(
          src,momTwist,timeBC,check,CGparamLoad,solvePrecision,
          masses,naik,load,cwmomsave(tsrc,tag,doSave),residuals))
    else:
        check = 'yes'
        load = ('fresh_ksprop',)
        invPSoct.append(KSsolveSet8Container(
          src,momTwist,timeBC,check,CGparamLoad,solvePrecision,
          masses,naik,load,cwmomsave(tsrc,tag,doSave),residuals))
    ## -- safeguard against missing
    if generateMissing and doLoad:
        for ss in invPSoct[-1].solveset:
            for prop in ss.propagator:
                if not(os.path.exists(prop.load[1])):
                    ss.check = 'yes'
                    prop.save = ('save_serial_scidac_ksprop',
                      prop.load[1])
                    prop.load = ('fresh_ksprop',)
    invPSoct[-1].addSolvesToSpectrum(spect)
## corner wall quarks
label = 'd'
save = ('forget_ksprop',)

qkPSlst = list() ## list of container objects
qkPSoct = list() ## list of octet objects
qkPSSmearlst = list() 
for inv in invPSoct:
  for i in range(inv.nmass):
    qkPSlst.append(QuarkIdentitySink8Container(
      inv,i,label,save))
    qkPSlst[-1].addQuarksToSpectrum(spect)
    qkPSoct.append(KSQuarkOctet(qkPSlst[-1]))
    spect.addQuarkOctet(qkPSoct[-1]) 
   
    for snk_smear_dict in snkSmearingParam:
        # Smear the identity quark
        label_ssnk = snk_smear_dict['tag']
        def snkGSmear(prop8, label,  save):
            if (snk_smear_dict)["type"] == "gaussian":
                return FatCovariantGaussianSink(prop8, snk_smear_dict, label, save)
            if (snk_smear_dict)["type"] == "laplacian":
                return FatCovariantLaplacianSink(prop8, snk_smear_dict["stride"], label, save)
        qkPSSmearlst.append(QuarkModificationSink8Container(inv,snkGSmear,i,label_ssnk,save))
        qkPSSmearlst[-1].addQuarksToSpectrum(spect)
        qkPSoct.append(KSQuarkOctet(qkPSSmearlst[-1]))
        spect.addQuarkOctet(qkPSoct[-1])
    

## corner wall quarks
label = 'd'
save = ('forget_ksprop',)
def cwseqsave(tsrc,momc,mass,doSave,cur,momi,ti,corner): ## TODO: finish, check
  if momc == '00':
   momstr = ''
  else:
   momstr = '_p'+''.join(str(x) for x in momc)
  ## construct suffix for current, momentum, t0
  extstr = '_x'+gen_hex(cur[0],cur[1])
  extstr = extstr +'_b'+str(corner)
  extstr = extstr +'_q'+''.join(str(x) for x in momi)
  extstr = extstr +'_i'+str(ti).zfill(3)
  if doSave:
    return (
      #'save_serial_scidac_ksprop', ## is this right?
      'save_serial_scidac_ks_source', ## this is correct NOW
      outsrc\
      +'/l'+str(dim[0])+str(dim[3])\
      +'_r'+trajc.zfill(4)+gcset\
      +'_m'+str(str(mass).split('.')[1].split(']')[0])\
      +'_ext'\
      +'_t'+str((tstart+tsrc)%t_size)\
      +'_$i'\
      +momstr\
      +extstr\
      +'_'+gStr+'.scidac' )
  else:
    return ('forget_source',)
  pass

def invseqsave(tsrc,momc,mass,doSave,corner,cur,momi,ti): ## TODO: finish, check
  if momc == '00':
   momstr = ''
  else:
   momstr = '_p'+''.join(str(x) for x in momc)
  ## construct suffix for current, momentum, t0
  extstr = '_x'+gen_hex(cur[0],cur[1])
  extstr = extstr +'_b'+str(corner) ## 0-7 for a corner subset, 8 for full
  extstr = extstr +'_q'+''.join(str(x) for x in momi)
  extstr = extstr +'_i'+str(ti).zfill(3)
  if doSave:
    return (
      'save_serial_scidac_ksprop', ## is this right?
      outprop\
      +'/l'+str(dim[0])+str(dim[3])\
      +'_r'+trajc.zfill(4)+gcset\
      #+'_m'+str(str(mass).split('.')[1])\
      +'_m'+str(str(mass).split('.')[1].split(']')[0])\
      +'_ext'\
      +'_t'+str((tstart+tsrc)%t_size)\
      +'_$i'\
      +momstr\
      +extstr\
      +'_'+gStr+'.prop' )
  else:
    return ('forget_ksprop',)
  pass

label = 'd'
## object lists

scSeqLst = list() ## list of vector base sources
scSeqOct = list() ## list of vector base source octets
invSeqLst = list() ## list of KS solve objects
qkSeqId = list() ## list of props with identity operators
qkSeqOct = list() ## list of octets of quarks
qkSeqLst = list() ## list of quark8 objects
qkSeqSolveLst = list() ## list of extended quarks after sink solves
qkSeqSolSmearLst = list()

for qrt,doSave\
    in zip(insQuartet,insDoSave):
  qk8 = qkPSlst[qrt[0]] ## assumes they are in order!
  mass = qk8.mass
  naik_eps = naik[0]
  tsrc = srcTimeslices[qrt[0]]
  ti = insTimeSep[qrt[1]]
  op = insCurrent[qrt[2]]
  opgam = gen_label(op[0],op[1])
  optag = gen_hex(op[0],op[1])
  mom = insMomenta[qrt[3]]
  tag = insTagMomenta[qrt[3]]
  tins = ((tstart+tsrc+ti)%t_size)
  subset = 'full' ## don't project! do that when loading
  cubeCorner = 8
  seqlabel = optag+'q'+''.join(str(x) for x in mom)+'t'+str(ti).zfill(3)+'c$i'
  save = ('forget_ksprop',)
  ## create the source objects
  #save = cwseqsave(tsrc,mom,mass,False,op,mom,tins,cubeCorner)

  qkSeqLst.append(KSExtSrcSink8Container(qk8,opgam,mom,tins,subset,seqlabel,save))
  qkSeqLst[-1].addQuarksToSpectrum(spect)

  # After applying appropriate sink spintaste, solve it 
  label = "ext$i"
  twist = (0,0,0)
  save = invseqsave(tsrc,mom,mass,False,8,op,mom,tins)
  qkSeqSolveLst.append(KSInverseSink8Container(qkSeqLst[-1],mass,naik_eps,u0,CGparam,
                                               residuals,solvePrecision,Uorigin,twist,timeBC,label,save))
  qkSeqSolveLst[-1].addQuarksToSpectrum(spect)
  qkSeqOct.append(KSQuarkOctet(qkSeqSolveLst[-1])) # add identity
  spect.addQuarkOctet(qkSeqOct[-1])

  for snk_smear_dict in snkSmearingParam:
    # After solving at sink, smear it
    def snkGSmear(prop8, label, save):
        if (snk_smear_dict)["type"] == "gaussian":
          return FatCovariantGaussianSink(prop8, snk_smear_dict, label, save)
        if (snk_smear_dict)["type"] == "laplacian":
          return FatCovariantLaplacianSink(prop8, snk_smear_dict["stride"], label, save)
    label_ssnk = snk_smear_dict['tag']


    tmpquark = list()
    for icorn in range(8): # 8 corners
        tmpquark.append(snkGSmear((qkSeqSolveLst[-1]).quark[icorn], 
                    label_ssnk, ("forget_ksprop",)))
    qkSeqSolSmearLst.append(tmpquark)

  # Keep them after all spin-taste are done
    iqkS = qkSeqSolSmearLst[-1]
    tmpquark = list()
    for ic in range(8):
        spect.addQuark(iqkS[ic])
      # dummy class HACK. So hacky i dont even know what to say
    class dummyclass:
        def __init__(self, qk8):
            self.quark = qk8
            return

    qkSeqOct.append(KSQuarkOctet(dummyclass(iqkS)))
    spect.addQuarkOctet(qkSeqOct[-1])

## CORNER WALLS - second time through

## do not spect.generate() between first and second
#spect.newGauge(Gauge(('continue',),u0,gFix,uSave,fatLink,Uorigin))
spect.GB3PointOn() ## turn on 3-points again!

## base corner wall sources
subset = 'full'
scaleFactor = None
save = ('forget_source',)
srcPSoct = list()
## inversion parameters
momTwist = (0,0,0)
timeBC = 'antiperiodic'
#CGparam = { 'restarts': 5, 'iters': 500 }
#CGparam = { 'restarts': 15, 'iters': 1000 } ## l3248
CGparam = { 'restarts': 300, 'iters': 8000 } ## l4864 ## TODO: have gconf dependent solution?
CGparamLoad = CGparam ## -- shouldn't matter, safe option
solvePrecision = 2
masses = [ tmass[0] ] ## always physical
naik = list(calcNaikEps(np.array(masses)*lattA))
naik = (0,0)
residuals = { 'L2': 1e-10, 'R2':0}

## --
## -- MESONS
## -- 

## -- N-point lists for mesons
#sink_op = ["G5T-G5T",]
sink_op = ["G5-G5", "GX-GX", "GY-GY", "GZ-GZ", "G5X-G5X", "G5Y-G5Y", "G5Z-G5Z", "G5T-G5T"]
no_current_insertion = 3 # number of current insertion 
insertion_op = "GT-GT" # This has to be consistent with the extended propagator 
if doMeson2pt:
  momentum = (0,0,0)
  mesonPSlocal = list()
  mesonRWlocal = list()
  for ic in range(no_current_insertion*len(sink_op)*8): # very hacky for 2pt, 3pt i=02, 3pt i=03
                       # multiply by eight as to include eight corners
                       # right now only work for local corner wall, maybe
    mesonPSlocal.append(list())
    mesonRWlocal.append(list())
    i = ic%8
    if int(ic/(len(sink_op)*8)) == 0:
        nametag = ""
        curr_str = "2pt" # no current insertion
    elif int(ic/(8*len(sink_op))) == 1:
        nametag = "-i02" # has to be consistent with extended quark!
        curr_str = insertion_op
    elif int(ic/(8*len(sink_op))) == 2:
        nametag = "-i03" # has to be consistent with extended quark!
        curr_str = insertion_op

    current_snk_op = sink_op[int(ic/8)%(len(sink_op))]
    mesonPSlocal[-1].append(MesonNpt(
     NameFormatCube('cw-0-%s-%s-corner%s'%(current_snk_op, curr_str, nametag),vecStr[i]),
     'p000',(1,'*',1.), (current_snk_op,),
     momentum,('EO','EO','EO')))
  def relOffset(i,t):
    l = [int(x) for x in '{0:b}'.format(i).zfill(3)]
    l.reverse()
    return (0,0,0,t)
    return tuple(l+[t])
  
  def mesonSpecFile(t,key):
    return ('save_corr_fnal',specFile2ptMesonPrefix() + specFileMidfix() 
      +'_t'+str(t).zfill(3)+"_"+key+"_"+ specFilePostfix())
    #return ('save_corr_fnal',specFilePrefix() + '_'+key+'_t'+str(t) + specFile2ptMesonPostfix())
  for tsrc,doLoad,qkList in zip(srcTimeslices,srcDoLoad,qkPSlst):
    if not(doLoad) or generateNewCorr:
     if doCWMeson2pt:
     # for i,qk in zip([0, 8],qkList.quark):
       for i in range(len(mesonPSlocal)):
         qk1 = qkList.quark[int(i%8)]
         if int(i/(8*len(sink_op))) == 0: # 2pt
             qk2 = qk1
         else:
             localoffset = 0 # for different links of source
             qk2 = ((qkSeqOct[int(i/(8*len(sink_op)))-1]).qk8).quark[localoffset+(i%8)] 
         spect.addMeson(MesonSpectrum(
          qk1,qk2,relOffset(i,(tstart+tsrc)%t_size),mesonPSlocal[i],
          mesonSpecFile((tstart+tsrc)%t_size,'cw')))
## if do2pt

## --
## -- GOLTERMAN-BAILEY 2-POINT
## --

## -- make a code for names
symCode = {}
symCode["S"] = "s"
symCode["A"] = "a"
symCode["M0"]   = "m0"
symCode["M1/2"] = "m5"
symCode["M1"]   = "m1"
gtsCode = {}
gtsCode["8"] = "8p"
gtsCode["8'"] = "8m"
gtsCode["16+"] = "16p"
gtsCode["16-"] = "16m"
namCode = ["nd","sl","xi","om"]
## -- list of allowed quark contents
cntList = {}
cntList[0]=["uuu","uud","udd","ddd"]
cntList[1]=["uus","uds","dds"]
cntList[2]=["uss","dss"]
cntList[3]=["sss"]
## -- organize allowed symmetries by number of strange quarks
symList = {}
symList[0]=["S","M1/2"]
symList[1]=["S","A","M1","M0"]
symList[2]=["S","M1/2"]
symList[3]=["S"]
## -- organize allowed classes by symmetry and GTS irrep
clsList = {}
clsList["S","8"]       = [1,2,3,5,61]
clsList["S","8'"]      = [7,41]
clsList["S","16+"]     = [2,3,41,61]
clsList["S","16-"]     = clsList["S","16+"]
clsList["A","8"]       = [7,41,61]
clsList["A","8'"]      = []
clsList["A","16+"]     = [41,61]
clsList["A","16-"]     = clsList["A","16+"]
clsList["M0","8"]     = [2,3,5,41,61,62]
clsList["M0","8'"]    = [41]
clsList["M0","16+"]   = [2,3,7,41,42,61,62]
clsList["M0","16-"]   = clsList["M0","16+"]
for sym in ["M1/2","M1"]:
  for gts in ["8","8'","16+","16-"]:
     clsList[sym,gts] = clsList["M0",gts]
pass

def gbBaryon2ptCorrelatorList(cnt,sym,gts,cls,phase,op,norm):
 gb2cor = list()
 for nstr in range(4):
  for xcnt in [xcnt for xcnt in cntList[nstr] if xcnt in cnt]:
   #- intersections of inclusive list and input list
   for xsym in [xsym for xsym in symList[nstr] if xsym in sym]:
    for xgts in [xgts for xgts in ["8","8'","16+","16-"] if xgts in gts]:
     for csrc in [csrc for csrc in clsList[xsym,xgts] if csrc in cls]:
      for csnk in [csnk for csnk in clsList[xsym,xgts] if csnk in cls]:
       #if csrc > csnk:
       #  continue
       if xsym[-1] == "*":
        barLabel = namCode[nstr] +"_"+ xcnt +"_"+ gtsCode[xgts] +"_"+ \
          symCode[xsym[:-1]] +"_"+ str(csrc) +"_"+ symCode[xsym] +"_"+ str(csnk)
        gb2cor.append(
          GBBaryon2pt(barLabel,(phase,op,norm),xgts,xsym[:-1],csrc,xsym,csnk))
       else:
        barLabel = namCode[nstr] +"_"+ xcnt +"_"+ gtsCode[xgts] +"_"+ \
          symCode[xsym] +"_"+ str(csrc) +"_"+ symCode[xsym] +"_"+ str(csnk)
        gb2cor.append(
          GBBaryon2pt(barLabel,(phase,op,norm),xgts,xsym,csrc,xsym,csnk))
 pass # all loops
 return gb2cor

## -- construct a list of correlators to do for each combo of inputs
##    both 2- and 3-point functions handled simultaneously
gb2cor = list()
gb2corBoth = list()
gb3cor = list()
phase = 1
op = '*'
factor = 1.
cnt = 'uud'
nam = 'nd'

cclsCut = [1,2,3,41,42,5,61,62,7] # all
kclsCut = [1,2,3,41,42,5,61,62,7] # all

#cclsCut = [5,]
#kclsCut = [5,]
#gtsCut = ["8","8'","16+","16-"]
gtsCut = ["16+","16-"]
## -- symmetric
## cube construction
#for sym in ["S","M1/2"]:
for sym in ["S"]:
 for cgts in gtsCut:
  #kgts = cgts # same source/sink gts (not required)
  for kgts in gtsCut:
   #if (kgts != cgts) and (not(cgts in ["16+","16-"]) or not(kgts in ["16+","16-"])):
   # continue
   if (kgts != cgts): continue
   for ccls in [xcls for xcls in clsList[sym,cgts] if xcls in cclsCut]:
    for kcls in [xcls for xcls in clsList[sym,kgts] if xcls in kclsCut]:
     barLabel = nam +"_b_"+ gtsCode[cgts] +"_"+ symCode[sym] +"_"+ \
       str(ccls) +"_"+ gtsCode[kgts] +"_"+ symCode[sym] +"_"+ str(kcls)
     if cgts == kgts:
      gb2cor.append(GBBaryon2pt(barLabel,(phase,op,factor),cgts,sym,ccls,kgts,sym,kcls,'point','cube'))
     gb2corBoth.append(GBBaryon2pt(barLabel,(phase,op,factor),cgts,sym,ccls,kgts,sym,kcls,'point','cube'))

### both constructions
#for cgts in gtsCut:
# #kgts = cgts # same source/sink gts (not required)
# for kgts in gtsCut:
#  if (kgts != cgts) and (not(cgts in ["16+","16-"]) or not(kgts in ["16+","16-"])):
#   continue
#  for ccls in [xcls for xcls in clsList[sym,cgts] if xcls in cclsCut]:
#   for kcls in [xcls for xcls in clsList[sym,kgts] if xcls in kclsCut]:
#    barLabel = nam +"_r_"+ gtsCode[cgts] +"_"+ symCode[sym] +"_"+ \
#      str(ccls) +"_"+ gtsCode[kgts] +"_"+ symCode[sym] +"_"+ str(kcls)
#    gb2corBoth.append(GBBaryon2pt(barLabel,(phase,op,factor),cgts,sym,ccls,kgts,sym,kcls,'corner'))

def baryonSpecFile(t,key):
  return ('save_corr_fnal',specFile2ptBaryonPrefix() + specFileMidfix()
    +'_t'+str(t).zfill(3)+"_"+key+"_"+ specFilePostfix())
def baryonSpecFileMom(t,key,tag):
  return ('save_corr_fnal',specFile2ptBaryonPrefix() + specFileMidfix()
    +'_t'+str(t).zfill(2)+"_"+key+"_p"+tag+"_"+ specFilePostfix())
def baryonSeqSpecFile(t,ti,momi,momk,cur,corner):
  momstr = '_p'+''.join(str(-x) for x in momk)
  extstr = '_x'+gen_hex(cur[0],cur[1])
  extstr = extstr +'_q'+''.join(str(x) for x in momi)
  extstr = extstr +'_i'+str(ti).zfill(3)
  extstr = extstr +'_b'+str(corner)
  return ('save_corr_fnal',specFile3ptBaryonPrefix() + specFileMidfix()
    +'_t'+str(t).zfill(3) +momstr+extstr +"_"+ specFilePostfix())

if True:
  if doSrcMomenta:
    for tsrc,doLoad,trip,tag in zip(srcTimeslices,srcDoLoad,srcTieMomenta,specTagMomenta):
      qk0 = qkPSoct[trip[0]]
      qk1 = qkPSoct[trip[1]]
      qk2 = qkPSoct[trip[2]]
      mom = tuple(x+y+z for x,y,z in zip(
       srcGenMomenta[trip[0]],srcGenMomenta[trip[1]],srcGenMomenta[trip[2]]))
      par = ('EO','EO','EO')
      if not(doLoad) or generateNewCorr:
        spect.addGBBaryon(GBBaryonSpectrum(
          qk0,qk1,qk2,(0,0,0,(tstart+tsrc)%t_size),gb2cor,'uud',
          baryonSpecFileMom((tstart+tsrc)%t_size,'cw',tag),mom,par))
  else:
    #for tsrc,doLoad,qkOct in zip(srcTimeslices,srcDoLoad,qkPSoct):
    for qkOct in qkPSoct:
      tsrc = srcTimeslices[0] # hack for multiple sink smearings
      doLoad = srcDoLoad[0] # hack for multiple sink smearings
      if not(doLoad) or generateNewCorr:
        spect.addGBBaryon(GBBaryonSpectrum(
          qkOct,qkOct,qkOct,(0,0,0,(tstart+tsrc)%t_size),gb2cor,'uud',
          baryonSpecFile((tstart+tsrc)%t_size,'cw'),(0,0,0),('EO','EO','EO')))
## if do2pt

#if do2pt:
#for j,(quart,qkInt,doCubeProject,cube,curtie)\
#in enumerate(zip(insQuartet,qkSeqOct,insDoProject,insProjectIndex,currTie)):

over_counter = 0     
for m, quart in enumerate(insQuartet):
     doCubeProject = False
     cube = True
     curtie = currTie[m]
     for ismear in range(len(snkSmearingParam)+1): # plus one to include identity
         qkInt = qkSeqOct[over_counter]
         qkSpec = qkPSoct[ismear]
         tsrc = srcTimeslices[0]
         doLoad = srcDoLoad[0]
         if len(srcTimeslices) > 1:
             raise ValueError
         ti = insTimeSep[quart[1]]
         if doCubeProject:
          cubeIdx = prn_cube(tsrc,ti,trajc,series,cube)
         else:
          subset = 'full'
          cubeIdx = 8
         for cur in curtie:
           #ti = insTimeSep[quart[1]]
           #cur = insCurrent[quart[2]]
           optag = gen_label(cur[0],cur[1])
           momi = tuple(x for x in insMomenta[quart[3]])
           momk = tuple(-x for x in insMomenta[quart[3]])
           #tins = ((tstart+tsrc+ti)%t_size)
           tins = ti ## actually want the separation here!
           if doCubeProject:
             spect.addGBBaryon(GBBaryonSpectrum(
              qkInt,qkSpec,qkSpec,(0,0,0,(tstart+tsrc)%t_size),gb2corBoth,'uud',
              baryonSeqSpecFile((tstart+tsrc)%t_size,tins,momi,momk,cur,cubeIdx),
              momk,('EO','EO','EO'),stidx=optag))
           else:
             spect.addGBBaryon(GBBaryonSpectrum(
              qkInt,qkSpec,qkSpec,(0,0,0,(tstart+tsrc)%t_size),gb2corBoth,'uud',
              baryonSeqSpecFile((tstart+tsrc)%t_size,tins,momi,momk,cur,cubeIdx),
              momk,('EO','EO','EO'),stidx=optag))
         over_counter += 1
         ## if do2pt

spect.generate()

#dflFile = wkflName + '-dataflow.yaml'
#file = open(dflFile,'w')
#file.write(yaml.dump(spect.dataflow(),default_flow_style=False))
