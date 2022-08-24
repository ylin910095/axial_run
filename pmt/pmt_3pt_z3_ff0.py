import numpy as np
import argparse
import hashlib
import os.path
import random
import sys
import yaml

from MILCprompts.MILCprompts import *
from MILCprompts.calcNaikEps import *
from MILCprompts.nameFormat import *

## user-defined parameters
pmt_param = {
  "u0": 0.855350,           ## u0 (dummy)
  'timeBC': "antiperiodic", ## time boundary condition
  'z3_sites_L': 2,          ## number of z3 noise sources per spatial dimension
  't0': 0,                  ## source timeslice
  #'tau_list': [3, 4, 5, 6], ## source-insertion separation times
  'tau_list': [3], ## source-insertion separation times
  'current': (15, 15),      ## spin-taste current insertion
  'snk_disp_3pt': 0,        ## spatial displacement of sink relative to source (0-7)
  ## momentum phase building blocks at source
  ## naming conventions assume to be positive only, but should work even if not the case
  'source_momenta': [(0,0,0), (1,0,0)],
  ## momentum at insertion (for each source momentum)
  ## key is source momentum, value is list of insertion momenta to create
  'insertion_momenta': [
    ( 0, 0, 0), ## 000-000, 100-100, 200-200, 300-300, 400-400
    (-1, 0, 0), ## 000-100, 100-000, 200-100, 300-200, 400-300
    #(-1,-1, 0), ## 100-010
    #(-1, 0,-1), ## 100-001
    #(-2, 0, 0), ## 000-200, 100-100, 200-000, 300-100, 400-200
    ],
  ## combinations of momentum phases needed at source for each 2-point correlator combo
  ## will ignore combos it can't create
  ## key is total source momentum
  '2pt_phase_combos': {
    ( 0, 0, 0): ((0,0,0),(0,0,0),(0,0,0)),
    ( 1, 0, 0): ((1,0,0),(0,0,0),(0,0,0)),
    ( 2, 0, 0): ((1,0,0),(1,0,0),(0,0,0)),
    ( 3, 0, 0): ((2,0,0),(1,0,0),(0,0,0)),
    ( 4, 0, 0): ((2,0,0),(2,0,0),(0,0,0)),
  },
  ## combinations of spectator momentum phases needed at source for each insertion momentum
  ## insertion momentum assumed to always come from (0,0,0) source momentum phase
  ## other sources always assumed to be positive
  ## p_src = -(p_ins + p_snk)
  ## key is insertion momentum, value is list of 2-tuples of spectator source phases to combine
  ## will ignore combos it can't create
  '3pt_phase_combos': {
    ( 0, 0, 0): [((0,0,0),(0,0,0)), ##  0 0 0
                 ((1,0,0),(0,0,0)), ## -1 0 0
                 ((1,0,0),(1,0,0)), ## -2 0 0
                 ((2,0,0),(1,0,0)), ## -3 0 0
                 ((2,0,0),(2,0,0)), ## -4 0 0
                ],
    (-1, 0, 0): [((0,0,0),(0,0,0)), ##  1 0 0
                 ((1,0,0),(0,0,0)), ##  0 0 0
                 ((1,0,0),(1,0,0)), ## -1 0 0
                 ((2,0,0),(1,0,0)), ## -2 0 0
                 ((2,0,0),(2,0,0)), ## -3 0 0
                ],
    (-1,-1, 0): [((1,0,0),(0,0,0)), ##  0-1 0
                ],
    (-1, 0,-1): [((1,0,0),(0,0,0)), ##  0 0-1
                ],
    (-2, 0, 0): [((0,0,0),(0,0,0)), ##  2 0 0
                 ((1,0,0),(0,0,0)), ##  1 0 0
                 ((1,0,0),(1,0,0)), ##  0 0 0
                 ((2,0,0),(1,0,0)), ## -1 0 0
                 ((2,0,0),(2,0,0)), ## -2 0 0
                ],
  },
  'gauss_smearing': {'r0': 1.0, 'N': 24}, ## source/sink smearing
  'inversion': {'L2': 1e-10, 'R2': 0, 'restarts': 50, 'iters': 8888}, # inverter control
}
prn_series = 0
MILC_prn_series = "rnd{}series".format( prn_series)
workflow_name = "workflow_gb_baryon_3pt"
job_name = "run_gb_baryon_3pt"

## python 3: replace with a reproducible hash for generating time sources
def myhash_str( _hashable):
  """A hashing utility function for creating reproducible string hashes from input."""
  return hashlib.sha224( str( _hashable).encode()).hexdigest()

def myhash( _hashable):
  """A hashing utility function for creating reproducible integer hashes from input."""
  return int( myhash_str( _hashable), 16)

parser = argparse.ArgumentParser( description="handle MILC input file generation")

## all of these arguments are required if not in testing mode
parser.add_argument(
  "-g", "--gauge_file", type=str,
  help="The path of the gauge configuration file to use.")
parser.add_argument(
  "-j", "--jobid", type=int,
  help="SLURM job id.")
parser.add_argument(
  "-s", "--directory_source", type=str,
  help="The path for source files to be written.")
parser.add_argument(
  "-p", "--directory_propagator", type=str,
  help="The path for propagator files to be written.")
parser.add_argument(
  "-c", "--directory_correlator", type=str,
  help="The path for correlator files to be written.")

## testing mode argument
parser.add_argument(
  "-t", "--test", action="store_true",
  help="Run in test mode. Ignore all other arguments.")

## flags
parser.add_argument(
  "--force_source_recreate", action="store_true",
  help="Do not load source files and create new.")
parser.add_argument(
  "--force_propagator_recreate", action="store_true",
  help="Do not load base propagator files and create new.")
parser.add_argument(
  "--force_sequential_recreate", action="store_true",
  help="Do not load sequential propagator files and create new.")

## do argument parsing
args = parser.parse_args()
if args.test:
  ## testing mode -- assign default values for everything else
  print( "testing mode")
  args.gauge_file = "/global/cfs/cdirs/m3652/hisq/l2464f211b600m0102m0509m635/gauge/l2464f211b600m0102m0509m635a-Coul.1000.ildg"
  args.jobid = 8888
  args.directory_correlator = "/test_dir_corr"
  args.directory_propagator = "/test_dir_prop"
  args.directory_source     = "/test_dir_src"

else:
  ## check that everything is here
  for attr in [
    "gauge_file", "jobid", "directory_source",
    "directory_propagator", "directory_correlator",
  ]:
      if getattr( args, attr) is None:
        print()
        print( "Argument \"{}\" required when not in testing mode".format( attr))
        print()
        parser.print_help()
        print()
        sys.exit()

## some flags supercede others
args.force_propagator_recreate = (
  args.force_propagator_recreate or args.force_source_recreate )
args.force_sequential_recreate = (
  args.force_sequential_recreate or args.force_propagator_recreate )

## parse gauge configuration filename to get more parameters
gconf = args.gauge_file.split( "/")[-1].split( "-")[0] ## "l2464f211b600m0102m0509m635a"
gcset = gconf[-1]                                      ## "a"
trajc = int( args.gauge_file.split(".")[-2])           ## 1000
qmass = [ float( "0.{}".format( gconf.split( "m")[i])) for i in range( 1, 3)]
dimL = int( gconf.split( "f")[0][1:3])
dimT = int( gconf.split( "f")[0][3:])
dim = [dimL]*3 +[dimT]

try:
  int( gcset)
  gcset = "a" ## default to "a" if not a letter
except:
  pass

## taken from Yin's script for posterity - needs updating
## Load pmt information from database
if 0 and (len(sys.argv) == 3 or len(sys.argv) == 7):
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



##
## --- gauge setup ---
##

# lattice stuff
sciDAC = None # { 'node': [ 4, 4, 4, 8 ], 'io': [ 4, 4, 4, 8 ] }
prompt = 0
spect = ks_spectrum(
  workflow_name, dim, np.abs( myhash( MILC_prn_series)),
  job_name, sciDAC, prompt)

#gFix = 'coulomb_gauge_fix'
gFix = 'no_gauge_fix' # already gauge fixed, don't change
gStr = 'coul'
fatLink = { 'weight': 0, 'iter': 0 }
uOrigin = [0,0,0,0]
uLoad = ('reload_parallel', args.gauge_file)
uSave = ('forget', )
u0 = pmt_param[ "u0"]
timeBC = pmt_param[ "timeBC"]

spect.newGauge( Gauge( uLoad, u0, gFix, uSave, fatLink, uOrigin, timeBC))
## to reuse same configuration -> save memory for orthogonal runs!
#spect.newGauge(Gauge(('continue',),u0,gFix,uSave,fatLink,uOrigin))

## turn on 3-point functionality!
spect.GB3PointOn()



##
## --- source generation ---
##

# randomize source points
# stop doing this so stupidly
def make_random_tstart( time_size, trajectory, series):
  ## -- approximately randomize over tstart, want something reproduceable
  def prn_timeslice( traj, series, dim):
    return myhash( myhash( str(traj) +"_" +str(series) +"timeslice")) % dim
  tstart = prn_timeslice( trajectory, series, time_size //2) *2 ## even only
  return tstart

def make_random_spatial_coor( spatial_size, trajectory, t0, series):
  def prn_spatial( traj, series, dim):
    return myhash( myhash( str(traj) +"_" +str(series) +"spatial")) % dim
  ## add some random large primes to series
  xstart = prn_spatial( trajectory, series+2161, spatial_size //2) *2 ## even only
  ystart = prn_spatial( trajectory, series+5023, spatial_size //2) *2 ## even only
  zstart = prn_spatial( trajectory, series+7919, spatial_size //2) *2 ## even only
  return [xstart, ystart, zstart]

### stupid fn to randomize cube index over tsrc,tins,trajectory,series and solve number
### make sure subsequent solves always give different cube indices
#def make_random_cube( tsrc, tins, traj, num, series):
#  def prn_cube( tsrc, tins, traj, series):
#    return myhash( myhash( str(tsrc) +"_" +str(tins) +"_" +str(traj) +"_" +str(series) +"cube"))
#  if num > 7:
#    raise IndexError("only 8 cube sites allowed; all used")
#  offset = [281, 659, 1069, 1373, 1657, 2129, 2617, 3079]
#  cleft = list( range( 8))
#  for i in range( num+1):
#    crand = prn_cube( tsrc, tins, traj, series +offset[i])
#    i8 = 8 -i
#    j = crand %i8
#    next_cube = cleft.pop( j)
#    crand //= i8
#  return next_cube

def z3_source_filename( trajc, z3sparseness, origin):
  out = args.directory_source +"/src_z3"
  out = out +"_t" +str( trajc).zfill( 4)
  out = out +"_s" +str( z3sparseness)
  out = out +"_x" +'.'.join([ str( x).zfill( 2) for x in origin ])
  out = out +".scidac"
  return out

## reference timeslice for all propagators
tstart = make_random_tstart( dimT, trajc, prn_series)
## number of sites to skip between z3 random source sites
z3sparseness = pmt_param[ "z3_sites_L"]
z3_skip = dimL //pmt_param[ "z3_sites_L"]
## offset of source from tstart
source_t0 = pmt_param[ "t0"]

## make the sparse Z3 sources
time_origin = int( (tstart +source_t0) %dimT)
space_origin = make_random_spatial_coor( dimL, trajc, time_origin, prn_series)
space_origin = [ (x %z3_skip) for x in space_origin ] ## reduce size of random block
full_origin = space_origin +[time_origin]
subset = "full"
ncolor = 3
scaleFactor = None
z3_file = z3_source_filename( trajc, z3sparseness, full_origin)

zero_mom = (0,0,0) ## use 0 momentum here, change momentum when loading
label = "z3dump"
save = ("save_serial_scidac_ks_source", z3_file)
## only generate if source file does not exist
if args.force_source_recreate or not( os.path.exists( z3_file)):
  z3src_dump = RandomSparseZ3Source(
    time_origin, space_origin, z3_skip, zero_mom, subset, label, save)
  spect.addBaseSource( z3src_dump)

z3_octets = {} ## keys are source momenta
## use the same z3 base source for all source momenta
for momentum in pmt_param[ "source_momenta"]:
  momstr = 'p' +''.join([ str( x) for x in momentum ])

  ## loaded with different momenta each time
  label = "z3" +momstr
  load = ("load_source", z3_file)
  save = ("forget_source",)
  z3src_load = VectorFieldSource(
    load, full_origin, ncolor, subset, momentum, scaleFactor, label, save)

  ## put into an octet container
  label = "z3" +momstr +"$i" ## pattern to replace in octet container
  save = ("forget_source",)
  isBaseSrc = True ## vector field is base source
  z3oct = GeneralSource8Container(
    z3src_load, label, save, isBaseSrc)
  z3_octets[ momentum] = z3oct
  z3oct.addSourcesToSpectrum( spect)
  spect.addSourceOctet( z3oct)



##
## --- propagator generation ---
##

def z3_propagator_filename( trajc, z3sparseness, origin, momentum):
  out = args.directory_propagator +"/prop_z3"
  out = out +"_t" +str( trajc).zfill( 4)
  out = out +"_s" +str( z3sparseness)
  out = out +"_x" +'.'.join([ str( x).zfill( 2) for x in origin ])
  out = out +"_m$m"
  out = out +"_p" +''.join([ str( x) for x in momentum ])
  out = out +"_$i"
  out = out +"_" +gStr
  out = out +".prop"
  return out

## inversion parameters
momTwist = (0,0,0)
CGparamFresh = {
  'restarts': pmt_param['inversion']['restarts'],
  'iters': pmt_param['inversion']['iters'],
}
CGparamLoad = CGparamFresh ## -- shouldn't matter, safe option
residuals = {
  'L2': pmt_param['inversion']['L2'],
  'R2': pmt_param['inversion']['R2'],
}
solvePrecision = 2
naik = (0,0)
masses = [ qmass[0] ] ## always physical

if args.force_source_recreate or not( os.path.exists( z3_file)):
  ## create a dummy solve for the random source generation
  check = "sourceonly"
  load = ("fresh_ksprop",)
  save = ("forget_ksprop",)
  dummy_elem = KSsolveElement(
    masses[0], naik, load, save, residuals)
  dummy_set = KSsolveSet(
    z3src_dump, momTwist, timeBC, check, CGparamLoad, solvePrecision)
  dummy_set.addPropagator( dummy_elem)
  spect.addPropSet( dummy_set)

z3_props = {}
z3_quarks = {}
z3_qkoct = {}
for momentum in z3_octets.keys():
  z3oct = z3_octets[ momentum]
  label = "z3" +momstr +"$i"
  z3_file = z3_propagator_filename( trajc, z3sparseness, full_origin, momentum)

  if args.force_propagator_recreate or not( os.path.exists( z3_file)):
    ## generate new
    check = "yes"
    load = ("fresh_ksprop",)
    save = ("save_parallel_scidac_ksprop", z3_file)
    CGparam = CGparamFresh
  else:
    ## reload existing
    check = "yes"
    load = ("reload_parallel_ksprop", z3_file)
    save = ("forget_ksprop",)
    CGparam = CGparamLoad

  ## add solves for these z3 sources
  z3prop = KSsolveSet8Container(
    z3oct, momTwist, timeBC, check, CGparam, solvePrecision,
    masses, naik, load, save, residuals)
  z3_props[ momentum] = z3prop
  z3prop.addSolvesToSpectrum( spect)

  ## add quark identity to interface with KSExtSrcSink
  save = ("forget_ksprop",)
  z3qk = QuarkIdentitySink8Container( z3prop, 0, label, save)
  z3qk8= KSQuarkOctet( z3qk)
  z3qk.addQuarksToSpectrum( spect)
  spect.addQuarkOctet( z3qk8)
  z3_quarks[ momentum] = z3qk
  z3_qkoct[ momentum] = z3qk8

##
## --- sequential solves ---
##

## gamma functions
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

def z3_sequential_filename(
  trajc, z3sparseness, origin, mass,
  insertion_momentum, insertion_tag, insertion_tau
):
    out = args.directory_propagator +"/seq_z3"
    out = out +"_t" +str( trajc).zfill( 4)
    out = out +"_s" +str( z3sparseness)
    out = out +"_x" +'.'.join([ str( x).zfill( 2) for x in origin ])
    out = out +"_m" +str( mass)[2:]
    out = out +"_$i"
    out = out +"_q" +''.join([ str( -x) for x in insertion_momentum ])
    out = out +"_t" +str( tau).zfill( 2)
    out = out +"_" +gStr
    out = out +".prop"
    return out

z3_seq_sources = {}
z3_seq_propagators = {}
z3_seq_quarks = {}
z3_seq_qkoct = {}
for source_momentum in z3_props.keys():
  if source_momentum == (0,0,0):
    ## sequential inversion block
    z3qk = z3_quarks[ source_momentum]
    op = pmt_param[ "current"]
    insertion_spin_taste = gen_label( op[0], op[1])
    insertion_tag = gen_hex( op[0], op[1])
    subset = "full"
    mass = masses[0]

    for tau in pmt_param[ "tau_list"]:
      insertion_time = time_origin +tau
      #
      for insertion_momentum in pmt_param[ "insertion_momenta"]:
        z3_file = z3_sequential_filename(
          trajc, z3sparseness, full_origin, mass,
          insertion_momentum, insertion_tag, tau)
        label = (
          insertion_tag
          +"q" +''.join([ str(-x) for x in insertion_momentum])
          +"t{:02d}".format( tau)
          +"c$i" )

        ## sequential source
        save = ("forget_ksprop",)
        z3seq_src = KSExtSrcSink8Container(
          z3qk, insertion_spin_taste, insertion_momentum,
          insertion_time, subset, label, save)
        z3_seq_sources[ tau, insertion_momentum] = z3seq_src
        z3seq_src.addQuarksToSpectrum( spect)

        ## sequential solve
        if args.force_sequential_recreate or not( os.path.exists( z3_file)):
          CGparam = CGparamFresh
          load = ("fresh_ksprop",)
          save = ("save_parallel_scidac_ksprop", z3_file)
        else:
          CGparam = CGparamLoad
          load = ("reload_parallel_ksprop", z3_file)
          save = ("forget_ksprop",)
        z3seq_inv = KSInverseSink8Container(
          z3seq_src, mass, naik, u0, CGparamFresh,
          residuals, solvePrecision, uOrigin,
          momTwist, timeBC, label, save)
        z3_seq_propagators[ tau, insertion_momentum] = z3seq_inv
        z3seq_inv.addQuarksToSpectrum( spect)

        ## sequential quark
        save = ("forget_ksprop",)
        z3seq_qk8= KSQuarkOctet( z3seq_inv)
        spect.addQuarkOctet( z3seq_qk8)
        z3_seq_qkoct[ tau, insertion_momentum] = z3seq_qk8

  ## end source_momentum == (0,0,0) block
  pass

##
## --- correlators ---
##

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
#namCode = ["nd","sl","xi","om"]
### -- list of allowed quark contents
#cntList = {}
#cntList[0]=["uuu","uud","udd","ddd"]
#cntList[1]=["uus","uds","dds"]
#cntList[2]=["uss","dss"]
#cntList[3]=["sss"]
### -- organize allowed symmetries by number of strange quarks
#symList = {}
#symList[0]=["S","M1/2"]
#symList[1]=["S","A","M1","M0"]
#symList[2]=["S","M1/2"]
#symList[3]=["S"]
## -- organize allowed classes by symmetry and GTS irrep
clsList = {}
clsList["S" ,"8"  ] = [1,2,3,5,61]
clsList["S" ,"8'" ] = [7,41]
clsList["S" ,"16+"] = [2,3,41,61]
clsList["S" ,"16-"] = clsList["S","16+"]
clsList["A" ,"8"  ] = [7,41,61]
clsList["A" ,"8'" ] = []
clsList["A" ,"16+"] = [41,61]
clsList["A" ,"16-"] = clsList["A","16+"]
clsList["M0","8"  ] = [2,3,5,41,61,62]
clsList["M0","8'" ] = [41]
clsList["M0","16+"] = [2,3,7,41,42,61,62]
clsList["M0","16-"] = clsList["M0","16+"]
for sym in ["M1/2","M1"]:
  for gts in ["8","8'","16+","16-"]:
     clsList[sym,gts] = clsList["M0",gts]

## construct a list of correlators to do for each combo of inputs
## both 2- and 3-point functions handled simultaneously
phase, op, factor = 1, '*', 1.
cnt = 'uud'

## functions for making NUCLEON-like operators
def make_gbcor_generic( sink_type, sink_disp_3pt, sym, src_gts, src_cls, snk_gts, snk_cls):
  out = []
  snk_disp_3pt = 0
  for ccls in src_cls:
    for kcls in snk_cls:
      barLabel = (
        "nd_b_"+
        gtsCode[src_gts]  +"_"+ symCode[sym] +"_"+ str(ccls) +"_"+
        gtsCode[snk_gts]  +"_"+ symCode[sym] +"_"+ str(kcls) +"_"+
        str(snk_disp_3pt) +"_"+ sink_type    +"_corner")
      out.append( GBBaryon2pt(
        barLabel,(phase,op,factor), src_gts,sym,ccls, snk_gts,sym,kcls,
        snk_disp_3pt, sink_type, "corner"
      ))
  return out

## zero momentum has same source and sink GTS
def make_gbcor_zero( sink_type, sink_disp_3pt, sym_list, gts_list):
  out = []
  for sym in sym_list:
    for gts in gts_list:
      cls_list = clsList[ sym, gts]
      out.extend( make_gbcor_generic(
        sink_type, sink_disp_3pt, sym, gts, cls_list, gts, cls_list))
  return out

## on-axis momentum may have different GTS overlap
## 8+ and 16+  or  8- and 16-
## symmetrization must be same
def make_gbcor_onaxis( sink_type, sink_disp_3pt, sym_list, gts_list):
  out = []
  gtsp, gtsm = ["8"], ["8'"]
  for sym in sym_list:
    for cgts in gts_list:
      for kgts in gts_list:
        if (
          ((cgts in gtsp) and (kgts in gtsm)) or
          ((kgts in gtsp) and (cgts in gtsm)) ): continue
        ccls_list = clsList[ sym, cgts]
        kcls_list = clsList[ sym, kgts]
        out.extend( make_gbcor_generic(
          sink_type, sink_disp_3pt, sym, cgts, ccls_list, kgts, kcls_list))
  return out

tagString = '00.'
def specFile2ptMesonPrefix():
  return args.directory_correlator +'/mes2pt.'+tagString
def specFile2ptBaryonPrefix():
  return args.directory_correlator +'/bar2pt.'+tagString
def specFile3ptBaryonPrefix():
  return args.directory_correlator +'/bar3pt.'+tagString

def specFileMidfix():
  return (
   'l'+str( dimL)+str( dimT)
   +'_r{}{:04d}'.format( gcset, trajc)
   +NameFormatMass( '_m$m', qmass[0]))
def specFilePostfix():
  return 'c{}.coul.cor'.format( args.jobid)

def baryonSpecFile( t, key):
  if isinstance( t, list) == False:
    return ('save_corr_fnal',
      specFile2ptBaryonPrefix() +specFileMidfix()
      +'_t{:03d}'.format( t) +"_" +key +"_"
      +specFilePostfix()
    )
  elif len( t) == 4: # x, y, z, t coordinate
    coors = ""
    coor_prefix = ["x","y","z","t"]
    for ic, ist in enumerate( t):
      coors += "_{:s}{:03d}".format( coor_prefix[ic], ist)
    return ('save_corr_fnal',
      specFile2ptBaryonPrefix() + specFileMidfix()
      +coors +"_" +key +"_"
      +specFilePostfix()
    )
  else:
    raise ValueError( "Unknown input")

def baryonSeqSpecFile( t, ti, momi, momk, cur, corner):
  momstr = '_p' +''.join( str(x) for x in momk)
  extstr = '_x' +gen_hex( cur[0], cur[1])
  extstr = extstr +'_q' +''.join( str(x) for x in momi)
  extstr = extstr +'_i{:03d}'.format( ti)
  extstr = extstr +'_b' +str( corner)
  if isinstance(t, list) == False:
    return ('save_corr_fnal',
      specFile3ptBaryonPrefix() +specFileMidfix()
      +'_t{:03d}'.format( t) +momstr +extstr +"_"
      +specFilePostfix()
    )
  elif len( t) == 4: # x, y, z, t coordinate
    coors = ""
    coor_prefix = ["x","y","z","t"]
    for ic, ist in enumerate( t):
      coors += "_{:s}{:03d}".format( coor_prefix[ic], ist)
    return ('save_corr_fnal',
      specFile3ptBaryonPrefix() +specFileMidfix()
      +coors +momstr +extstr +"_"
      +specFilePostfix()
    )
  else:
    raise ValueError( "Unknown input")

for src_momentum in pmt_param[ "2pt_phase_combos"].keys():
  snk_momentum = src_momentum
  qk0_momentum, qk1_momentum, qk2_momentum = pmt_param[ "2pt_phase_combos"][ src_momentum]
  ## skip combos that can't be created
  if not( qk0_momentum in pmt_param[ "source_momenta"]): continue
  if not( qk1_momentum in pmt_param[ "source_momenta"]): continue
  if not( qk2_momentum in pmt_param[ "source_momenta"]): continue

  ## do true 2pt
  qk0 = z3_octets[ qk0_momentum]
  qk1 = z3_octets[ qk1_momentum]
  qk2 = z3_octets[ qk2_momentum]
  sink_type = "point"
  spin_taste = gen_label( 127, 127) ## 2pt
  if src_momentum == (0,0,0):
    key = "z3s{}".format( pmt_param[ "z3_sites_L"])
    specfn = baryonSpecFile( time_origin, key)
    #corrs = make_gbcor_zero( sink_type, 0, ["S", "M1/2"], ["8","8'","16+","16-"])
    corrs = make_gbcor_zero( sink_type, 0, ["S"], ["16+","16-"])
    spect.addGBBaryon( GBBaryonSpectrum(
      qk0, qk1, qk2, (0,0,0,time_origin), corrs, "uud", specfn,
      snk_momentum, ('EO','EO','EO')))
  else:
    key = "z3s{}_p{}{}{}".format( pmt_param[ "z3_sites_L"], *src_momentum)
    specfn = baryonSpecFile( time_origin, key)
    corrs = make_gbcor_onaxis( sink_type, 0, ["S"], ["8'","16+","16-"])
    spect.addGBBaryon( GBBaryonSpectrum(
      qk0, qk1, qk2, (0,0,0,time_origin), corrs, "uud", specfn,
      snk_momentum, ('EO','EO','EO'), stidx=spin_taste))

moth0_momentum = (0,0,0)
for tau in pmt_param[ "tau_list"]:
  insertion_time = time_origin +tau
  #
  for insertion_momentum in pmt_param[ "insertion_momenta"]:
    qk0 = z3_seq_qkoct[ tau, insertion_momentum]
    for spec0_momentum, spec1_momentum in pmt_param[ "3pt_phase_combos"][ insertion_momentum]:
      ## skip combos that can't be created
      if not( spec0_momentum in pmt_param[ "source_momenta"]): continue
      if not( spec1_momentum in pmt_param[ "source_momenta"]): continue
      src_momentum = tuple( np.array( spec0_momentum    ) + np.array( spec1_momentum) )
      snk_momentum = tuple( np.array( insertion_momentum) + np.array( src_momentum  ) )
  
      qk1 = z3_octets[ spec0_momentum]
      qk2 = z3_octets[ spec1_momentum]
      key = "z3s{}".format( pmt_param[ "z3_sites_L"])
      spin_taste = gen_label( *pmt_param[ "current"])
      specfn = baryonSeqSpecFile(
        time_origin, insertion_time,
        insertion_momentum, snk_momentum,
        pmt_param[ "current"], 0)
      if src_momentum == (0,0,0) and snk_momentum == (0,0,0):
        corrs = make_gbcor_zero( sink_type, 0, ["S"], ["16+","16-"])
        spect.addGBBaryon( GBBaryonSpectrum(
          qk0, qk1, qk2, (0,0,0,time_origin), corrs, "uud", specfn,
          snk_momentum, ('EO','EO','EO'), stidx=spin_taste))
      else:
        corrs = make_gbcor_onaxis( sink_type, 0, ["S"], ["8'","16+","16-"])
        spect.addGBBaryon( GBBaryonSpectrum(
          qk0, qk1, qk2, (0,0,0,time_origin), corrs, "uud", specfn,
          snk_momentum, ('EO','EO','EO'), stidx=spin_taste))


##
## --- finish ---
##

spect.generate()

