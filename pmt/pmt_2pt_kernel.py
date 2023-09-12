import sys, os
import numpy as np
from MILCprompts.MILCprompts import *
from MILCprompts.calcNaikEps import *
from MILCprompts.nameFormat import *

if sys.version_info[0] != 2:
    import zlib
    # redefine hash function for tsrc randomization
    # notice that this is incompatible with tsrc generated from python2!!
    def hash(x):
        return zlib.adler32(bytes(str(x),encoding='utf8'))
else:
    raise Exception("Don't use python2")

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

def pmt_2pt_kernel(spect=None, **param_dict):
    # Inputs to the pmt file
    pmt_param = param_dict['pmt_param']
    projDir = param_dict['projDir']
    outprop = param_dict['outprop']
    jobid = param_dict['jobid']
    
    # Gauge file
    gaugefile = param_dict['gaugefile']
    layout = param_dict['layout']
    
    # Sources
    srcTimeslices = param_dict['srcTimeslices']
    srcTypeList = param_dict['srcTypeList']
    srcBaseList = param_dict['srcBaseList']
    srcTagMomenta = param_dict['srcTagMomenta']
    srcLabelOverride = param_dict['srcLabelOverride']
    srcDoLoad = param_dict['srcDoLoad']
    srcDoSave = param_dict['srcDoSave']
    srcSolve = param_dict['srcSolve']
    srcSmearingParam = param_dict['srcSmearingParam']
    srcLabelOverride = param_dict['srcLabelOverride']
    
    # Quarks 
    basePropList = param_dict['basePropList']
    quarkTypeList = param_dict['quarkTypeList']
    quarkSmearParam = param_dict['quarkSmearParam']
    quarkLabelOverride = param_dict['quarkLabelOverride']
    quarkSinkTypeList = param_dict['quarkSinkTypeList']
    
    
    # Parse gauge file name
    gconf = (gaugefile.split("/")[-1]).split("-")[0]
    try:
        str(int(gconf[-1]))
    except:
        gconf = gconf[:-1]
    trajc = gaugefile.split(".")[-2]
    gcset = gaugefile.split("-")[-2][-1]
    try:
        str(int(gcset))
        gcset = "a" # default silent set a
    except:
        pass
    tmass = [float('0.'+gconf.split('m')[i]) for i in range(1,3)]
    smass = [gconf.split('m')[i] for i in range(1,3)]
    dim = [gconf.split('f')[0][1:3],gconf.split('f')[0][1:3],
            gconf.split('f')[0][1:3],gconf.split('f')[0][3:]]
    
    # Make random tsrc using hash function
    s_size=int(dim[0])
    t_size=int(dim[3])
    tstart = make_random_tstart(t_size, trajc)
    
    ## Not used
    u0 = 1

    ## -- if a source/propagator is missing when loaded, generate a new one instead of terminating
    ##    save the newly generated object to the place where it was looking for it before
    generateMissing = True

    ## -- if reloading a cw source, do the 2-point baryon/meson tie-ups again
    generateNewCorr = True

    # Flag for multiRHS. This option only works properly if GRID is compiled
    # with MILC that has multisrc flag enabled
    multisource = False
    
    
    # Making gauge configs
    gFix = 'no_gauge_fix' # already gauge fixed, don't change
    gStr = 'coul'
    uSave = ('forget', )
    fatLink = { 'weight': 0, 'iter': 0 }
    Uorigin = [0,0,0,0]
    timeBC = "antiperiodic"
    if spect is None:
        # lattice stuff
        prompt = 0
        wkflName = 'workflow-test-brw'
        ## putting numbers at end doesn't change seed by much     
        rndSeries = 'rnd0series'
        spect = ks_spectrum(wkflName, dim, np.abs(hash(rndSeries)),
                            'job-test-baryon-ks-spectrum', layout, prompt)
        uLoad = ('reload_parallel', gaugefile)
        spect.newGauge(Gauge(uLoad,u0,gFix,uSave,fatLink,Uorigin,timeBC))
    else:
        spect.newGauge(Gauge(('continue',),u0,gFix,uSave,fatLink,Uorigin,timeBC))
    
    
    ## CORNER WALLS - first time through
    ## base corner wall sources
    subset = 'full'
    scaleFactor = None
    save = ('forget_source',)
    srcPSoct = list()

    for i,(tsrc,srctype,srcbase,tag,srclabel) in enumerate(zip(
        srcTimeslices,srcTypeList,srcBaseList,srcTagMomenta,srcLabelOverride)):
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
            ptdisp = [list(np.array(space_origin)+np.array(ivdisp))+[torigin] for ivdisp in vecdisp]
            #for iptcorner in range(8):
            label = "pt%s"%vecStr[0]
            if srclabel is not None:
                label = srclabel
                
            ptsrc = PointSource(origin=ptdisp[0],
                                subset=subset,scaleFactor=None,label="pt%s"%vecStr[0],save=save)
            #ptsrc_list.append(PointSource(origin=ptdisp[0],
            #                subset=subset,scaleFactor=None,label="pt%s"%vecStr[0],save=save))
            srcPSoct.append([ptsrc,]) # technically not an octet but wtv
            spect.addBaseSource(ptsrc)
            #srcPSoct.append(BaseSource8Container(src=ptsrc_list, label="Notused"))
            #srcPSoct[-1].addSourcesToSpectrum(spect)
            #spect.addSourceOctet(srcPSoct[-1])
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
                save = ("forget_source",)
                try: # if the previous source is a modified source
                    xport_list.append(ParallelTransportModSource(startSource=srcPSoct[srcbase][0], # only use the first one!
                                            disp=int(np.sum(vecdisp[iptcorner])),
                                            dir=dir_str_list,
                                            label=label,
                                            save=save))
                except: # if the previous source ia a base source
                    xport_list.append(ParallelTransportModSource(startSource=srcPSoct[srcbase][0], # only use the first one!
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
    CGparam = { 'restarts': pmt_param['inversion']['restarts'],
                'iters': pmt_param['inversion']['iters'] }
    CGparamLoad = CGparam ## -- shouldn't matter, safe option
    solvePrecision = 2
    masses = [ pmt_param['mass'] ] # inversion mass
    naik = (0,0)
    residuals = { 'L2': pmt_param['inversion']['L2'],
                'R2': pmt_param['inversion']['R2']}

    ## corner wall solves
    invPSoct = list()
    def cwmomsave(tsrc,mom,doSave):
        if mom == '00':
            momstr = ''
        else:
            momstr = '_p'+mom
        if doSave:
            return (
            'save_parallel_scidac_ksprop',
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
    for tsrc,src,doLoad, doSave, doSolve, tag in zip(
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
    #spect.newGauge(Gauge(('continue',),u0,gFix,uSave,fatLink,Uorigin))

    ## base corner wall sources
    subset = 'full'
    scaleFactor = None
    save = ('forget_source',)
    srcPSoct = list()
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
    gb2corBoth = list()
    def make_gb2cor(sink_type):
        gb2cor = list()
        phase = 1
        op = '*'
        factor = 1.
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
    
    tagString = '01.'
    def specFile2ptBaryonPrefix():
        return projDir+'/bar2pt.'+tagString
        #return scratchDir+'/bar2pt.'+tagString
    def specFileMidfix():
        return 'l'+str(dim[0])+str(dim[3])\
        +'_r'+gcset+trajc.zfill(4)\
        +NameFormatMass('_m$m',tmass[0])
    def specFilePostfix():
        return 'c'+jobid+'.coul.cor'

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

    for (qkOct, sinkType) in zip(qkPSoct, quarkSinkTypeList):
        tsrc = srcTimeslices[0] # hack for multiple sink smearings
        torigin = (tstart+tsrc)%t_size
        doLoad = srcDoLoad[0] # hack for multiple sink smearings

        # Determine if we use point src
        space_origin = make_random_spatial_coor(torigin, trajc, s_size)
        rx = space_origin[0]
        ry = space_origin[1]
        rz = space_origin[2]
        tsinp = space_origin + [torigin]
        if not(doLoad) or generateNewCorr:
            spect.addGBBaryon(GBBaryonSpectrum(
            qkOct,qkOct,qkOct,(rx,ry,rz,(tstart+tsrc)%t_size),make_gb2cor(sinkType),'uud',
            baryonSpecFile(tsinp,'ptcw'),(0,0,0),('EO','EO','EO')))

    return spect