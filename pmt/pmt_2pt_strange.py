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

if len(sys.argv) != 1 and len(sys.argv) != 6:
  print("%s usage: gauge_location jobid outcoor outprop outsrc"%sys.argv[0])
  sys.exit()
elif len(sys.argv) == 1:
  print("Testing")
  gaugefile = "/projects/AxialChargeStag/hisq/l6496f211b630m0012m0363m432/gauge/l6496f211b630m0012m0363m432p-Coul.315.ildg"
  jobid = '88888'
  projDir='/this_is_test_proj_Dir'
  lqcdDir=projDir
  outprop = '/test'
  outprop_temp = '/hpcgpfs01/work/lqcd/axial/yin/data/prod015_dispersion/prop'
  outsrc = '/test/src'
else:
  gaugefile = sys.argv[1]
  jobid = sys.argv[2]
  projDir = sys.argv[3]
  outprop = sys.argv[4]
  outsrc = sys.argv[5]
  lqcdDir = projDir

  
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

## -- if a source/propagator is missing when loaded, generate a new one instead of terminating
##    save the newly generated object to the place where it was looking for it before
generateMissing = True

## -- if reloading a cw source, do the 2-point baryon/meson tie-ups again
generateNewCorr = True

# Flip the sink corner to the opposite end
# This is necessary for some non-zero momentum currents (g4z, g5 and so on)
# This will only flip the sink for 3pt functions at non-zero momentum
flip_sink = False

# Flag for multiRHS. This option only works properly if GRID is compiled
# with MILC that has multisrc flag enabled
multisource = True

# Randomize source points
def make_random_tstart(time_size, trajectory):
  ## -- approximately randomize over tstart, want something reproduceable
  series = 0
  def prn_timeslice(traj,series,dim):
    return hash(hash(str(traj)+str(series)+"x")) % dim
  ## -- prn sometimes gets stuck in infinite loop
  ##    altering with rnchg gets out of loop
  ##    constructed in a way to prevent breaking those that did work after few iters
  rniter = 0
  rnchg = ''
  tstart = -1
  while (tstart % 2 == 1):
    tstart = prn_timeslice(str(int(trajectory)+max(tstart,0))+rnchg,series,time_size)
    rniter += 1
    if rniter % 10 == 9:
      rnchg = rnchg + str(tstart)
  return int(tstart)
def make_random_spatial_coor(t0, trajectory, spatial_size):
  def _iter_hash(inp):
    return str(hash(str(inp)))
  def _make_even(num):
    if num%2 == 0: return num
    else: return(num+1)
  r = []
  for ic in range(3):
    ik = 0
    hashstr = str(t0) + "_random_" + str(trajectory) + "imrandomstring"
    while ik < ic+1:
      hashstr = _iter_hash(hashstr+ "imanotherrandomstring") 
      ik += 1
    r.append(_make_even(int(hashstr))%spatial_size)
  return r
s_size=int(dim[0])
t_size=int(dim[3])
tstart = make_random_tstart(t_size, trajc)

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

num_sets = 1
srcTimeslices = tuple([0]*100) # point, gauss smear, xport, and cornerwall
srcTypeList = tuple(["point", "xport", "gauss"]*num_sets)
srcBaseList = tuple([None, 0, 1]*num_sets)
srcDoLoad = tuple([False, False, False]*num_sets) 
srcDoSave = (False, False, False)
srcSolve = (False, False, True) # do we want to solve this set of propagators? It is 
                         # useful we only want to use it as base source to have modified 
                         # sources but we do not want to solve for the base sources.

# Decide whether to put random coordinate labels in the correlator names
ptsrc_label = False

## TODO: make sure doMomenta updated to doSrcMomenta
doSrcMomenta = False
srcGenMomenta = ((0,0,0),(0,0,0),(0,0,0),(0,0,0)) # momentum on source inversions
srcTagMomenta = ('00','00','00','00') # tag for momentum on source
srcZeroMomenta = (0,0,0,0) # index of base source to use

# Smearing controls
gparam_list = []
r0_list = [3.0,]
iter_list = [50,]
for i in range(len(r0_list)):
    tmp_gparam = {
                  'type': 'gaussian',
                  'stride': 2,
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

srcSmearingParam = (None, None, gparam_list[0], None)
srcLabelOverride = (None, None, gparam_list[0]['tag'], None)

## Quark controls
basePropList = (0, 0) # only count those that are solved
quarkTypeList = ("identity", "gauss")
quarkBaseList = (None, None,)
quarkSmearParam = (None, gparam_list[0])
quarkLabelOverride = (None, None) # if not None, override the default labeling
quarkSinkTypeList = ("point", "point")

## parameters to make insertions with
insTimeSep = (3,4,5,6,7)
insCurrent = ((0,0),(11,11),)  
#insMomenta = ((0,0,0),(0,0,1))
insMomenta = ((0,0,0),) # sequential momentum inversions
insTagMomenta = ('00','00') # tag for momentum

# STEP BY STEP INPUT GUIDE!
# FOLLOW THIS! OR YOU WILL MAKE MISTAKES!
# 1. Change insSpec 
# 2. Change insSrcIndex
# 3. Chnage insDoProject
# 4. Change currTie
# 5. Check consistency between all entries above
# 6. Check python pmt output
# 7. SUBMIT!
## 5-tuples of (quark,tsrc,timesep,current,momenta) indices
# quark has to be identity!
#insSpec = ((0,0,1,1), (0,1,1,1), (0,2,1,1),(0,3,1,1)) #set1 done PROJECT IT
insSpec = ((0,0,0,1,1),(0,0,1,1,1),(0,0,2,1,1),(0,0,3,1,1),(0,0,4,1,1))
insSpec = ((0,0,1,1,1),)
insSpec = ()
insSrcDoSave = tuple(False for x in insSpec) # whetever to save extend quark at sink

## decoupled from other source objects
insSrcIndex = (0,1,2,3,4,5)
insDoLoad = tuple(False for x in insSrcIndex)
insDoSave = tuple(False for x in insDoLoad)

insDoProject = (False,False,False,False,False,False)
cornerIter = 0 ## number 0-7, higher numbers choose different corners
insProjectIndex = tuple(cornerIter for x in insSrcIndex)

## Threept tieup quark list -- need to come from the same propagators
seqTieList = [(1,), (1,), (1,), (1,), (1,)]  
seqTieList = [(1,)]
seqTieList = []
if len(seqTieList) != len(insSpec):
    raise ValueError("Need to specify tieup for all sequential solves!")

## specific tie-ups for specific currents
currTieScalar = ((0, 0), )
currTieAz = ((11,11),)
currTieV4 = ((8, 8),)
currTieG5TG5T = ((7,7),)
currTieV4VX4 = ((8, 9),)
currTieG5XG5 = ((14, 15),)
currTieAx = ((14,14),)
currTieG5XGXT = ((14, 9),)
currTieG5XG5 = ((14,15),)
currTieGTG5 = ((8, 15),)
currTieG5XG5Y = ((14, 13), )
currTieG4G5X = ((8, 14),)
currTieAll = ((7,7),(14,14),(13,13),(11,11),(8,8),(1,1),(2,2),(4,4))
#currTie = (currTieAll,currTieAll,currTieAz,currTieAz)
#currTie = (currTieV4, currTieV4)
#currTie = (currTieAll,currTieAz)
#currTie = [currTieAz]*len(insSpec)
currTie = currTieG5TG5T
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
  #return scratchDir+'/mes2pt.'+tagString
def specFile2ptBaryonPrefix():
  return projDir+'/bar2pt.'+tagString
  #return scratchDir+'/bar2pt.'+tagString

## TODO: fix for new 3-point functions
def specFile3ptBaryonPrefix():
  return projDir+'/bar3pt.'+tagString
  #return scratchDir+'/bar3pt.'+tagString
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


for i,(tsrc,srctype,srcbase,idx,mom,tag,srclabel) in enumerate(zip(
    srcTimeslices,srcTypeList,srcBaseList, srcZeroMomenta,srcGenMomenta,srcTagMomenta,srcLabelOverride)):
  if srctype == "wall":
    label = 'cw$i'
    if srclabel is not None:
      label = srclabel
    ## do zero momentum as base source!
    srcPSoct.append(CornerWall8Container(
      str((tstart+tsrc)%t_size),subset,scaleFactor,label,save))
    srcPSoct[-1].addSourcesToSpectrum(spect)
    spect.addSourceOctet(srcPSoct[-1])
  elif srctype == "point":
    label = 'pt$i'
    if srclabel is not None:
      label = srclabel
    ## do zero momentum as base source!
    torigin = int((tstart+tsrc)%t_size)
    ptsrc_list = [] # octet
    # (x, y, z, t)
    vecdisp = [[0,0,0],[1,0,0],[0,1,0],[1,1,0],
                [0,0,1],[1,0,1],[0,1,1],[1,1,1]]

    space_origin = make_random_spatial_coor(torigin, trajc, s_size)
    ptsrc_label = True
    ptdisp = [list(np.array(space_origin)+np.array(ivdisp))+[torigin] for ivdisp in vecdisp]
    for iptcorner in range(8):
        label = "pt%s"%vecStr[0]
        if srclabel is not None:
          label = srclabel
        origin = 0  
        ptsrc_list.append(PointSource(origin=ptdisp[0],
                          subset=subset,scaleFactor=None,label="pt%s"%vecStr[0],save=save))
    srcPSoct.append(BaseSource8Container(src=ptsrc_list, label="Notused"))
    srcPSoct[-1].addSourcesToSpectrum(spect)
    spect.addSourceOctet(srcPSoct[-1])
  elif srctype == "xport":
    # HACK, do parallel transport
    torigin = int((tstart+tsrc)%t_size)
    # (x, y, z, t)
    vecdisp = [[0,0,0],[1,0,0],[0,1,0],[1,1,0],
                [0,0,1],[1,0,1],[0,1,1],[1,1,1]]
    xport_list = []
    for iptcorner in range(8):
        label="xport%s"%vecStr[iptcorner]
        if srclabel is not None:
          label = srclabel
        dir_str = ["x","y","z"]
        dir_str_list = [dir_str[ict] for ict, imk in enumerate(vecdisp[iptcorner])
                        if imk != 0]
        #save = ("save_serial_scidac_ks_source", outsrc+"/%s.txt"%("_".join(dir_str_list))) 
        save = ("forget_source",)
        try: # if the previous source is a modified source
            xport_list.append(ParallelTransportModSource(startSource=srcPSoct[srcbase].modifd[0],
                                    disp=int(np.sum(vecdisp[iptcorner])),
                                    dir=dir_str_list,
                                    label=label,
                                    save=save))
        except: # if the previous source ia a base source
            xport_list.append(ParallelTransportModSource(startSource=srcPSoct[srcbase],
                                    disp=int(np.sum(vecdisp[iptcorner])),
                                    dir=dir_str_list,
                                    label=label,
                                    save=save))
    srcPSoct.append(BaseSource8Container(src=xport_list, label="Notused"))
    srcPSoct[-1].addSourcesToSpectrum(spect, baseSrc=False)
    spect.addSourceOctet(srcPSoct[-1])
  elif srctype == "gauss":
      label = srcSmearingParam[i]['tag']
      if srclabel is not None:
        label = srclabel
      save = ("forget_source", )
      def smearFunc(src8,label,save):
          if (srcSmearingParam[i])["type"]  == "gaussian":
              return FatCovariantGaussian(srcSmearingParam[i], label, save, src8)
          if (srcSmearingParam[i])["type"] == "laplacian":
              return FatCovariantLaplacian((srcSmearingParam[i])["stride"], label, save, src8)
      srcPSoct.append(GeneralSource8Modification(srcPSoct[srcbase],smearFunc,label,save))
      srcPSoct[-1].addSourcesToSpectrum(spect)
      spect.addSourceOctet(srcPSoct[-1])

## inversion parameters
momTwist = (0,0,0)
#CGparam = { 'restarts': 5, 'iters': 500 }
#CGparam = { 'restarts': 15, 'iters': 1000 } ## l3248
CGparam = { 'restarts': 50, 'iters': 5000 } ## l4864 ## TODO: have gconf dependent solution?
CGparamLoad = CGparam ## -- shouldn't matter, safe option
solvePrecision = 2
masses = [ tmass[1] ] ## always physical
naik = list(calcNaikEps(np.array(masses)*lattA))
naik = (0,0)
residuals = { 'L2': 1e-12, 'R2': 0}

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
      #lqcdDir+'/prop'+prodDir+'/'+campaign\
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

# Propagators sets
for tsrc,src,doLoad,doSave, doSolve, tag in zip(
        srcTimeslices,srcPSoct,srcDoLoad,srcDoSave,srcSolve,srcTagMomenta):
    if not doSolve:
        continue

    if doLoad:
        check = 'yes'
        load = ('reload_parallel_ksprop',cwmomsave(tsrc,tag,True)[1])
        cgparamtemp = CGparamLoad
    else:
        check = 'yes'
        load = ('fresh_ksprop',)
        cgparamtemp = CGparam

    if not multisource:
        invPSoct.append(KSsolveSet8Container(
          src,momTwist,timeBC,check,CGparamLoad,solvePrecision,
          masses,naik,load,cwmomsave(tsrc,tag,doSave),residuals))
    else:
        ss = KSsolveSetNContainer_MultiSource(momTwist,timeBC,check,cgparamtemp,solvePrecision,
                                              masses,naik,residuals)
        ss.appendSolveSet(src,load,cwmomsave(tsrc,tag,doSave))
        invPSoct.append(ss)

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

# Quark specifications
qkPSlst = list() ## list of container objects
qkPSoct = list() ## list of octet objects
qkPSSmearlst = list() 

for (baseProp, quarkType, quarkSmear, quarkLabel) in zip(
              basePropList, quarkTypeList, quarkSmearParam, quarkLabelOverride):
  inv = invPSoct[baseProp]
  if inv.nmass > 1:
    raise ValueError("Scripts can only do one mass inversion!")
  if quarkType == "identity":
    label = 'd'
    save = ('forget_ksprop',)
    if quarkLabel is not None:
      label = quarkLabel
    if multisource:
        multisrc_indx = 0
    else:
        multisrc_indx = None      
    qkPSlst.append(QuarkIdentitySink8Container(
                   inv,0,label,save,multisource=multisource,multisrc_prop_idx=multisrc_indx))
    qkPSlst[-1].addQuarksToSpectrum(spect)
    qkPSoct.append(KSQuarkOctet(qkPSlst[-1]))
    spect.addQuarkOctet(qkPSoct[-1])
  elif quarkType == "gauss":
    label = quarkSmear['tag']
    if quarkLabel is not None:
      label = quarkLabel
    save = ('forget_ksprop',)
    def snkGSmear(prop8, label,  save):
        if (quarkSmear)["type"] == "gaussian":
            return FatCovariantGaussianSink(prop8, quarkSmear, label, save)
        if (quarkSmear)["type"] == "laplacian":
            return FatCovariantLaplacianSink(prop8, 2, label, save)
    if multisource:
        multisrc_indx = 0
    else:
        multisrc_indx = None
    qkPSSmearlst.append(QuarkModificationSink8Container(inv,snkGSmear,0,label,save,
                        multisource=multisource,multisrc_prop_idx=multisrc_indx))
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
      #lqcdDir+'/src'+prodDir+'/'+campaign\
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
      #lqcdDir+'/prop'+prodDir+'/'+campaign\
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
qkIntOct = list()
qkSeqLst = list() ## list of quark8 objects
qkSeqSolveLst = list() ## list of extended quarks after sink solves
qkSeqSolSmearLst = list()

for ic,(spec,doSave)\
    in enumerate(zip(insSpec,insSrcDoSave)):
  qk8 = qkPSlst[spec[0]] ## assumes they are in order!
  if quarkTypeList[spec[0]] != "identity":
      raise ValueError("Sequential solve must come from identity quark tyep!")
  mass = qk8.mass
  naik_eps = naik[0]
  tsrc = srcTimeslices[spec[1]]
  ti = insTimeSep[spec[2]]
  op = insCurrent[spec[3]]
  opgam = gen_label(op[0],op[1])
  optag = gen_hex(op[0],op[1])
  mom = insMomenta[spec[4]]
  
  # momentum conservation
  mom = list(mom)
  for im in range(len(mom)):
      mom[im] = -mom[im] 

  tins = ((tstart+tsrc+ti)%t_size)
  subset = 'full' ## don't project! do that when loading
  cubeCorner = 8
  seqlabel = optag+'q'+''.join(str(x) for x in mom)+'t'+str(ti).zfill(3)+'c$i'
  save = ('forget_ksprop',)
  ## create the source objects
  if doSave:
   save = cwseqsave(tsrc,mom,mass,doSave,op,mom,tins,cubeCorner)
  qkSeqLst.append(KSExtSrcSink8Container(qk8,opgam,mom,tins,subset,seqlabel,save))
  qkSeqLst[-1].addQuarksToSpectrum(spect)

  # After applying appropriate sink spintaste, solve it 
  label = "cw0" # if used directly, it must be using as corner wall sink
  twist = (0,0,0)
  save = ('forget_ksprop', )
  qkSeqSolveLst.append(KSInverseSink8Container(qkSeqLst[-1],mass,naik_eps,u0,CGparam,
                                               residuals,solvePrecision,Uorigin,twist,timeBC,label,save))
  qkSeqSolveLst[-1].addQuarksToSpectrum(spect)
  qkSeqOct.append(KSQuarkOctet(qkSeqSolveLst[-1])) # already identity
  spect.addQuarkOctet(qkSeqOct[-1])


  seqTie = seqTieList[ic]
  for seqTieIndex in seqTie:
      if basePropList[seqTieIndex] != basePropList[spec[0]]:
          raise ValueError("3pt tie up need to come from the same propagators")
      quarkType = quarkTypeList[seqTieIndex]
      quarkLabel = quarkLabelOverride[seqTieIndex]
      quarkSmear = quarkSmearParam[seqTieIndex]

      if quarkType == "identity":
        qkIntOct.append(qkSeqOct[-1]) # already identity

      elif quarkType == "gauss":
        label = quarkSmear['tag']
        if quarkLabel is not None:
          label = quarkLabel
        save = ('forget_ksprop',)
        def snkGSmear(prop8, label,  save):
            if (quarkSmear)["type"] == "gaussian":
                return FatCovariantGaussianSink(prop8, quarkSmear, label, save)
        tmpquark = list()
        for icorn in range(8): # 8 corners
            tmpquark.append(snkGSmear((qkSeqSolveLst[-1]).quark[icorn],
                              label, ("forget_ksprop",)))
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
        qkSeqLst.append(dummyclass(iqkS))
        qkIntOct.append(KSQuarkOctet(qkSeqLst[-1]))
        spect.addQuarkOctet(qkIntOct[-1])

## CORNER WALLS - second time through

## do not spect.generate() between first and second
#spect.newGauge(Gauge(('continue',),u0,gFix,uSave,fatLink,Uorigin))
spect.GB3PointOn() ## turn on 3-points again!

## base corner wall sources
subset = 'full'
scaleFactor = None
save = ('forget_source',)
srcPSoct = list()

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
    for xgts in [xgts for xgts in ["16+","16-"] if xgts in gts]:
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


def make_gb3cor(sink_type):
    gb2corBoth = list()
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
         gb2corBoth.append(GBBaryon2pt(barLabel,(phase,op,factor),cgts,sym,ccls,kgts,sym,kcls,sink_type,'corner'))
    return gb2corBoth

def make_gb3cor_nonzero(sink_type):
    gb2corBoth = list()
    cclsCut = [1,2,3,41,42,5,61,62,7] # all
    kclsCut = [1,2,3,41,42,5,61,62,7] # all

    #cclsCut = [5,]
    #kclsCut = [5,]
    #gtsCut = ["8","8'","16+","16-"]
    gtsCut = ["16+","16-"]
    gtsCut = ["16+", "8", "16-","8'"]
    allowed_sets = [set(["16+", "8"]), set (["16-", "8'"])]
    ## -- symmetric
    ## cube construction
    #for sym in ["S","M1/2"]:
    for sym in ["S"]:
     if flip_sink:
      snk_sym = sym+"*"
     else:
      snk_sym = sym
     for cgts in gtsCut:
      #kgts = cgts # same source/sink gts (not required)
      for kgts in gtsCut:
       if (kgts != cgts) and set([kgts, cgts]) not in allowed_sets:
         continue
       for ccls in [xcls for xcls in clsList[sym,cgts] if xcls in cclsCut]:
        for kcls in [xcls for xcls in clsList[sym,kgts] if xcls in kclsCut]:
         barLabel = nam +"_b_"+ gtsCode[cgts] +"_"+ symCode[sym] +"_"+ \
           str(ccls) +"_"+ gtsCode[kgts] +"_"+ symCode[sym] +"_"+ str(kcls)
         gb2corBoth.append(GBBaryon2pt(barLabel,(phase,op,factor),cgts,sym,ccls,kgts,snk_sym,kcls,sink_type,'corner'))
    return gb2corBoth

def make_gb2cor(sink_type):
  gb2cor = list()
  phase = 1
  op = '*'
  factor = 1.
  cnt = 'uud'
  nam = 'nd'

  cclsCut = [1,2,3,41,42,5,61,62,7] # all
  kclsCut = [1,2,3,41,42,5,61,62,7] # all

  #cclsCut = [5,]
  #kclsCut = [5,]
  gtsCut = ["8'"]
  #gtsCut = ["16-","16+"]
  ## -- symmetric
  ## cube construction
  for sym in ["S","M1/2"]:
   for cgts in gtsCut:
    #kgts = cgts # same source/sink gts (not required)
    for kgts in gtsCut:
     #if (kgts != cgts) and (not(cgts in ["16+","16-"]) or not(kgts in ["16+","16-"])):
     # continue
     #if (kgts != cgts): continue
     for ccls in [xcls for xcls in clsList[sym,cgts] if xcls in cclsCut]:
      for kcls in [xcls for xcls in clsList[sym,kgts] if xcls in kclsCut]:
       barLabel = nam +"_b_"+ gtsCode[cgts] +"_"+ symCode[sym] +"_"+ \
         str(ccls) +"_"+ gtsCode[kgts] +"_"+ symCode[sym] +"_"+ str(kcls)
       if cgts == kgts:
        gb2cor.append(GBBaryon2pt(barLabel,(phase,op,factor),cgts,sym,ccls,kgts,sym,kcls,sink_type,'corner'))
       gb2corBoth.append(GBBaryon2pt(barLabel,(phase,op,factor),cgts,sym,ccls,kgts,sym,kcls,sink_type,'corner'))
  return gb2cor

def make_gb2cor_nonzero(sink_type):
  gb2cor = list()
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
  gtsCut = ["16+", "8", "16-","8'"]
  allowed_sets = [set(["16+", "8"]), set (["16-", "8'"])]
  ## -- symmetric
  ## cube construction
  #for sym in ["S","M1/2"]:
  for sym in ["S"]:
   for cgts in gtsCut:
    #kgts = cgts # same source/sink gts (not required)
    for kgts in gtsCut:
     if (kgts != cgts) and set([kgts, cgts]) not in allowed_sets:
      continue
     #if (kgts != cgts): continue
     for ccls in [xcls for xcls in clsList[sym,cgts] if xcls in cclsCut]:
      for kcls in [xcls for xcls in clsList[sym,kgts] if xcls in kclsCut]:
       barLabel = nam +"_b_"+ gtsCode[cgts] +"_"+ symCode[sym] +"_"+ \
         str(ccls) +"_"+ gtsCode[kgts] +"_"+ symCode[sym] +"_"+ str(kcls)
       #if cgts == kgts:
       gb2cor.append(GBBaryon2pt(barLabel,(phase,op,factor),cgts,sym,ccls,kgts,sym,kcls,sink_type,'corner'))
       gb2corBoth.append(GBBaryon2pt(barLabel,(phase,op,factor),cgts,sym,ccls,kgts,sym,kcls,sink_type,'corner'))
  return gb2cor

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
  if isinstance(t, list) == False:
    return ('save_corr_fnal',specFile2ptBaryonPrefix() + specFileMidfix()
      +'_t'+str(t).zfill(3)+"_"+key+"_"+ specFilePostfix())
  else:
    if len(t) != 4: # x, y, z, t coordinate
      raise ValueError("Unknow input")
    coors = ""
    coor_prefix = ["x","y","z","t"]
    for ic, ist in enumerate(t):
      coors += "_%s%s"%(coor_prefix[ic], str(ist).zfill(3))
    return ('save_corr_fnal',specFile2ptBaryonPrefix() + specFileMidfix()
      + coors +"_"+key+"_"+ specFilePostfix())
def baryonSpecFileMom(t,key,tag):
  if isinstance(t, list) == False:
    return ('save_corr_fnal',specFile2ptBaryonPrefix() + specFileMidfix()
      +'_t'+str(t).zfill(3)+"_"+key+"_p"+tag+"_"+ specFilePostfix())
  else:
    if len(t) != 4: # x, y, z, t coordinate
      raise ValueError("Unknow input")
    coors = ""
    coor_prefix = ["x","y","z","t"]
    for ic, ist in enumerate(t):
      coors += "_%s%s"%(coor_prefix[ic], str(ist).zfill(3))
    return ('save_corr_fnal',specFile2ptBaryonPrefix() + specFileMidfix()
      + coors +"_"+key+"_p"+tag+"_"+ specFilePostfix())
def baryonSeqSpecFile(t,ti,momi,momk,cur,corner):
  momstr = '_p'+''.join(str(x) for x in momk)
  extstr = '_x'+gen_hex(cur[0],cur[1])
  extstr = extstr +'_q'+''.join(str(x) for x in momi)
  extstr = extstr +'_i'+str(ti).zfill(3)
  extstr = extstr +'_b'+str(corner)
  if isinstance(t, list) == False:
    return ('save_corr_fnal',specFile3ptBaryonPrefix() + specFileMidfix()
      +'_t'+str(t).zfill(3) +momstr+extstr +"_"+ specFilePostfix())
  else:
    if len(t) != 4: # x, y, z, t coordinate
      raise ValueError("Unknow input")
    coors = ""
    coor_prefix = ["x","y","z","t"]
    for ic, ist in enumerate(t):
      coors += "_%s%s"%(coor_prefix[ic], str(ist).zfill(3))
    return ('save_corr_fnal',specFile3ptBaryonPrefix() + specFileMidfix()
      + coors +momstr+extstr +"_"+ specFilePostfix())

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
    for (qkOct, sinkType) in zip(qkPSoct, quarkSinkTypeList):
      tsrc = srcTimeslices[0] # hack for multiple sink smearings
      torigin = (tstart+tsrc)%t_size
      doLoad = srcDoLoad[0] # hack for multiple sink smearings

      # Determine if we use point src
      if ptsrc_label:
        space_origin = make_random_spatial_coor(torigin, trajc, s_size)
        rx = space_origin[0]
        ry = space_origin[1]
        rz = space_origin[2]
        tsinp = space_origin + [torigin]
      else:
        tsinp = torigin

      for sinktiemom in insMomenta:
          if sinktiemom == (0,0,0):
              if not(doLoad) or generateNewCorr:
                spect.addGBBaryon(GBBaryonSpectrum(
                  qkOct,qkOct,qkOct,(rx,ry,rz,(tstart+tsrc)%t_size),make_gb2cor(sinkType),'uud',
                  baryonSpecFile(tsinp,'ptsrc'),(0,0,0),('EO','EO','EO')))
          else:
                tag = '%s%s%s'%(sinktiemom[0],sinktiemom[1],sinktiemom[2])
                spect.addGBBaryon(GBBaryonSpectrum(
                  qkOct,qkOct,qkOct,(rx,ry,rz,(tstart+tsrc)%t_size),make_gb2cor_nonzero(sinkType),'uud',
                  baryonSpecFileMom(tsinp,'ptsrc',tag),sinktiemom,('EO','EO','EO')))
          

#if do2pt:
#for j,(quart,qkInt,doCubeProject,cube,curtie)\
#in enumerate(zip(insSpec,qkSeqOct,insDoProject,insProjectIndex,currTie)):

for m, spec in enumerate(insSpec):
     qkInt = qkIntOct[m]
     seqTie = seqTieList[m]
     for ic, seqTieIndex in enumerate(seqTie):
        doCubeProject = False
        cube = True
        curtie = currTie[0]
        qkInt = qkIntOct[ic+m*len(seqTie)]
        qkSpec = qkPSoct[seqTieIndex]
        sinkType = quarkSinkTypeList[seqTieIndex]
        tsrc = srcTimeslices[spec[1]]
        doLoad = srcDoLoad[0]
        #if len(srcTimeslices) > 1:
        #    raise ValueError
        ti = insTimeSep[spec[2]]

        tsrc = srcTimeslices[0] # hack for multiple sink smearings
        torigin = (tstart+tsrc)%t_size
        doLoad = srcDoLoad[0] # hack for multiple sink smearings
        # Determine if we use point src
        if ptsrc_label:
          space_origin = make_random_spatial_coor(torigin, trajc, s_size)
          rx = space_origin[0]
          ry = space_origin[1]
          rz = space_origin[2]
          tsinp = space_origin + [torigin]
        else:
          tsinp = torigin

        if doCubeProject:
          cubeIdx = prn_cube(tsrc,ti,trajc,series,cube)
        else:
          subset = 'full'
          cubeIdx = 8
          optag = gen_label(curtie[0],curtie[1])
          momi = tuple(-x for x in insMomenta[spec[4]])
          momk = tuple(x for x in insMomenta[spec[4]])
          #tins = ((tstart+tsrc+ti)%t_size)
          tins = ti ## actually want the separation here!
          if momk == (0,0,0):
            spect.addGBBaryon(GBBaryonSpectrum(
              qkInt,qkSpec,qkSpec,(0,0,0,(tstart+tsrc)%t_size),make_gb3cor(sinkType),'uud',
              baryonSeqSpecFile(tsinp,tins,momi,momk,curtie,cubeIdx),
              momk,('EO','EO','EO'),stidx=optag))
          else:
            spect.addGBBaryon(GBBaryonSpectrum(
              qkInt,qkSpec,qkSpec,(0,0,0,(tstart+tsrc)%t_size),make_gb3cor_nonzero(sinkType),'uud',
              baryonSeqSpecFile(tsinp,tins,momi,momk,curtie,cubeIdx),
              momk,('EO','EO','EO'),stidx=optag))


spect.generate()

#dflFile = wkflName + '-dataflow.yaml'
#file = open(dflFile,'w')
#file.write(yaml.dump(spect.dataflow(),default_flow_style=False))
