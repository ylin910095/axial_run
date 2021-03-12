import sys
import textwrap
from Cheetah.Template import Template
from nameFormat import *

def base36(n):
    """Convert a positive integer to a base36 string."""
    alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    base = 36
    if n <= 0:
        return str(0)
    nb = ''
    while n != 0:
        n, i = divmod(n,base)
        nb = alphabet[i] + nb
        pass
    return nb

def oppMom(mom):
    """Take negative of momentum coordinates."""
    return [-p for p in mom]

vecStr = ['0','x','y','xy','z','zx','yz','xyz'] * 3 # in case of multiple sources

class Geometry:
    """Lattice geometry, machine layout (SciDAC) and seed for random nuber generator."""
    _Template = """
    #== ${_classType} ==
    prompt ${prompt}
    nx ${dim[0]}
    ny ${dim[1]}
    nz ${dim[2]}
    nt ${dim[3]}
    #if $layout is not None:
    node_geometry #echo ' '.join(map(str,$layout.node))#
    ionode_geometry #echo ' '.join(map(str,$layout.io))#
    #end if
    iseed ${seed}
    job_id ${jobID}"""
    def __init__(self,dim,seed,jobID,prompt,layout):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.dim = dim
        self.seed = seed
        self.jobID = jobID
        self.layout = layout
        self.prompt = prompt
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class Gauge:
    """The SU3 gauge field, gauge fixing and APE link smearing."""
    _Template = """
    #== ${_classType} ==
    #echo ' '.join($load)#
    u0 ${u0}
    ${gFix}
    #echo ' '.join($save)#
    staple_weight ${fatLink.weight}
    ape_iter ${fatLink.iter}
    coordinate_origin #echo ' '.join(map(str,$origin))#
    time_bc $time_bc"""
    def __init__(self,load,u0,gFix,save,fatLink,origin,time_bc):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.load = load
        self.u0 = u0
        self.gFix = gFix
        self.save = save
        self.fatLink = fatLink
        self.origin = origin
        self.time_bc = time_bc
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.load) > 1:
            requires.append(self.load[1])
            pass
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class PointSource:
    """Point base source."""
    _Template = """
    #== source ${id}: ${_classType} ==
    point
    field_type KS
    subset ${subset}
    origin #echo ' '.join(map(str,$origin))#
    #if $scaleFactor is not None:
    scale_factor ${scaleFactor}
    #end if
    source_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,origin,subset,scaleFactor,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.origin = origin
        self.subset = subset
        self.scaleFactor = scaleFactor
        self.label = label
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        pass
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class EvenMinusOddWallSource:
    """evenminusodd_wall base source."""
    _Template = """
    #== source ${id}: ${_classType} ==
    evenminusodd_wall
    subset ${subset}
    t0 ${tsrc}
    #if $scaleFactor is not None:
    scale_factor ${scaleFactor}
    #end if
    source_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,subset,tsrc,scaleFactor,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.subset = subset
        self.tsrc = tsrc
        self.scaleFactor = scaleFactor
        self.label = label
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        pass
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class EvenAndOddWallSource:
    """evenandodd_wall base source."""
    _Template = """
    #== source ${id}: ${_classType} ==
    evenandodd_wall
    subset ${subset}
    t0 ${tsrc}
    #if $scaleFactor is not None:
    scale_factor ${scaleFactor}
    #end if
    source_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,subset,tsrc,scaleFactor,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.subset = subset
        self.tsrc = tsrc
        self.scaleFactor = scaleFactor
        self.label = label
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        pass
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class CornerWall8Container:
    """Container for the 8 CornerWallSources of the unit cube.
       For use with gauge fixing only."""
    _Template = """
    #== source octet ${id}: ${_classType} ==
    octet $source[0].id $source[1].id $source[2].id $source[3].id $source[4].id $source[5].id $source[6].id $source[7].id"""
    def __init__(self,tsrc,subset,scaleFactor,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.source = list()
        for i in range(8):
            self.source.append(CornerWallSource(i,tsrc,subset,scaleFactor,
              NameFormatCube(label,vecStr[i]),NameFormatCube(save,vecStr[i]))) ## num->str
            #NameFormatCube(label,i),NameFormatCube(save,i)))
            pass
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def addSourcesToSpectrum(self,spect):
        for i in range(8):
            spect.addBaseSource(self.source[i])
            pass
        return

class VectorField8Container:
    """Container for the 8 VectorFieldSource of the unit cube."""
    _Template = """
    #== source octet ${id}: ${_classType} ==
    octet $source[0].id $source[1].id $source[2].id $source[3].id $source[4].id $source[5].id $source[6].id $source[7].id"""
    def __init__(self,load,origin,ncolor,subset,
                 momentum,scaleFactor,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.source = list()
        self.load = load
        self.origin = origin
        self.ncolor = ncolor
        self.subset = subset
        self.momentum = momentum
        self.scaleFactor = scaleFactor
        self.label = label
        self.save = save

        # Loop over corners
        for i in range(8):
            cLoad = NameFormatCube(self.load, vecStr[i])
            cLabel = NameFormatCube(label,vecStr[i])
            cSave = NameFormatCube(self.save, vecStr[i])
            appendV = VectorFieldSource(cLoad,self.origin,self.ncolor,self.subset,
                                        self.momentum,self.scaleFactor,cLabel,cSave)
            self.source.append(appendV) 

        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def addSourcesToSpectrum(self,spect):
        for i in range(8):
            spect.addBaseSource(self.source[i])
            pass
        return

class BaseSource8Container:
    """Container for loading any set of 8 sources for all corners of the unit cube.
    """
    _Template = """
    #== source octet ${id}: ${_classType} ==
    octet $source[0].id $source[1].id $source[2].id $source[3].id $source[4].id $source[5].id $source[6].id $source[7].id"""
    def __init__(self,src,label):#,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.source = list()
        self.modifd = list()
        for source in src:
          self.source.append(source)
        #try:
        #    self.tsrc = src[0].origin[3]
        #except:
        #    self.tsrc = src[0].tsrc
        #pass
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def addSourcesToSpectrum(self,spect, baseSrc=True):
        for i in range(8):
            if baseSrc:
              spect.addBaseSource(self.source[i])
              pass
            else:
              spect.addModSource(self.source[i])
        return

class GeneralSource8Container:
    """Container for loading any source and creating 7 point-split variants
       for all corners of the unit cube.  """
    _Template = """
    #== source octet ${id}: ${_classType} ==
    octet $source[0].id $modifd[0].id $modifd[1].id $modifd[2].id $modifd[3].id $modifd[4].id $modifd[5].id $modifd[6].id"""
    def __init__(self,src,label,save,useLinks,isBaseSrc):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.source = list()
        self.modifd = list()
        self.source.append(src)
        try:
            self.tsrc = src.origin[3]
        except:
            self.tsrc = src.tsrc
        pass
        self.isBaseSrc = isBaseSrc
        for i in range(7):
            self.modifd.append(ParallelTransportModSource(self.source[0],
              useLinks,len(vecStr[i+1]),vecStr[i+1],
              NameFormatCube(label,vecStr[i+1]),NameFormatCube(save,vecStr[i+1])))
            pass
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def addSourcesToSpectrum(self,spect):
        if self.isBaseSrc:
          spect.addBaseSource(self.source[0])
        else:
          spect.addModSource(self.source[0])
          pass
        for i in range(7):
            spect.addModSource(self.modifd[i])
            pass
        return


class ExtSrc8Modification:
    """Container for applying a KSExtSrc to an octet of sources.
       Applies the input function to all the sources in the octet. Input function
       should have only three arguments: source,label,save."""
    _Template = """
    #== source octet ${id}: ${_classType} ==
    octet $modifd[0].id $modifd[1].id $modifd[2].id $modifd[3].id $modifd[4].id $modifd[5].id $modifd[6].id $modifd[7].id"""
    def __init__(self,src8,spin_taste_op,momentum,tsrc,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.src8 = src8
        self.spin_taste_op = spin_taste_op
        self.momentum = momentum
        self.tsrc = tsrc 
        self.label = label
        self.save = save
        self.source = list()
        self.modifd = list()
        self.nSrc = len(src8.source)

        # If the source is a base source
        for i in range(self.nSrc): 
            cLabel = NameFormatCube(label,vecStr[i])
            cSave = NameFormatCube(save,vecStr[i])
            appendV = KSExtSrc(self.src8.source[i],self.spin_taste_op,
                             self.momentum,self.tsrc,cLabel,cSave)
            self.modifd.append(appendV)

        # If the source is a modified source
        for i in range(8-self.nSrc): 
            cLabel = NameFormatCube(label,vecStr[i+self.nSrc])
            cSave = NameFormatCube(save,vecStr[i+self.nSrc])
            appendV = KSExtSrc(self.src8.modifd[i],self.spin_taste_op,
                             self.momentum,self.tsrc,cLabel,cSave)
            self.modifd.append(appendV)
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def addSourcesToSpectrum(self,spect):
        for i in range(8):
            spect.addModSource(self.modifd[i])
            pass
        return


class GeneralSource8Modification:
    """Container for applying a source modification to an octet of sources.
       Applies the input function to all the sources in the octet. Input function
       should have only three arguments: source,label,save."""
    _Template = """
    #== source octet ${id}: ${_classType} ==
    octet $modifd[0].id $modifd[1].id $modifd[2].id $modifd[3].id $modifd[4].id $modifd[5].id $modifd[6].id $modifd[7].id"""
    def __init__(self,src8,inputFn,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.src8 = src8
        self.source = list()
        self.modifd = list()
        self.nSrc = len(src8.source)
        for i in range(self.nSrc):
            self.modifd.append(inputFn(self.src8.source[i],
              NameFormatCube(label,vecStr[i]),
              NameFormatCube(save,vecStr[i])))
            pass
        for i in range(8-self.nSrc):
            self.modifd.append(inputFn(self.src8.modifd[i],
              NameFormatCube(label,vecStr[i+self.nSrc]),
              NameFormatCube(save,vecStr[i+self.nSrc])))
            pass
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def addSourcesToSpectrum(self,spect):
        for i in range(8):
            spect.addModSource(self.modifd[i])
            pass
        return

class BaryonRandomWallSource:
    """Random wall base source for baryons."""
    _Template = """
    #== source ${id}: ${_classType} ==
    baryon_random_wall
    subset ${subset}
    t0 ${tsrc}
    momentum #echo ' '.join(map(str,$momentum))#
    source_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,tsrc,subset,momentum,scaleFactor,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.subset = subset
        self.tsrc = tsrc
        self.momentum = momentum
        self.scaleFactor = scaleFactor
        self.label = NameFormatCube(label,vecStr[0])
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        pass
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class RandomColorWallSource:
    """Random color wall base source."""
    _Template = """
    #== source ${id}: ${_classType} ==
    random_color_wall
    subset ${subset}
    t0 ${tsrc}
    ncolor ${ncolor}
    momentum #echo ' '.join(map(str,$momentum))#
    source_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,tsrc,subset,ncolor,momentum,scaleFactor,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        #self.corner = vecStr[corner]
        #self.corner = corner ## num->str
        self.subset = subset
        self.tsrc = tsrc
        self.ncolor = ncolor
        self.momentum = momentum
        self.scaleFactor = scaleFactor
        self.label = NameFormatCube(label,vecStr[0])
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        pass
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class CornerWallSource:
    """Wall base source."""
    _Template = """
    #== source ${id}: ${_classType} ==
    #if $corner == 0:
    corner_wall
    #else:
    corner_wall_${corner}
    #end if
    field_type KS
    subset ${subset}
    t0 ${tsrc}
    #if $scaleFactor is not None:
    scale_factor ${scaleFactor}
    #end if
    source_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,corner,tsrc,subset,scaleFactor,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.corner = vecStr[corner]
        #self.corner = corner ## num->str
        self.subset = subset
        self.tsrc = tsrc
        self.scaleFactor = scaleFactor
        self.label = label
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        pass
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class VectorFieldSource:
    """Color vector field base source input from a file. For KS only for now."""
    _Template = """
    #== source ${id}: ${_classType} ==
    vector_field
    field_type KS
    subset ${subset}
    origin #echo ' '.join(map(str,$origin))#
    #echo ' '.join($load)#
    ncolor ${ncolor}
    momentum #echo ' '.join(map(str,$momentum))#
    #if $scaleFactor is not None:
    scale_factor ${scaleFactor}
    #end if
    source_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,load,origin,ncolor,subset,momentum,scaleFactor,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.load = load
        self.origin = origin
        self.ncolor = ncolor
        self.subset = subset
        self.momentum = momentum
        self.scaleFactor = scaleFactor
        self.label = label
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.load) > 1:
            requires.append(self.load[1])
            pass
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class DiracFieldSource:
    """Dirac (spin and color) base source."""
    _Template = """
    #== source ${id}: ${_classType} ==
    dirac_field
    subset ${subset}
    origin #echo ' '.join(map(str,$origin))#
    #echo ' '.join($load)#
    nsource #echo 4 * ${ncolor}#
    momentum #echo ' '.join(map(str,$momentum))#
    #if $scaleFactor is not None:
    scale_factor ${scaleFactor}
    #end if
    source_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,load,origin,ncolor,subset,momentum,scaleFactor,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.load = load
        self.origin = origin
        self.ncolor = ncolor
        self.subset = subset
        self.momentum = momentum
        self.scaleFactor = scaleFactor
        self.label = label
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.load) > 1:
            requires.append(self.load[1])
            pass
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class KSExtSrc:
    """Extended source modifier option for KS base sources."""
    _Template = """
    #== source ${id}: ${_classType} ==
    source ${src.id}
    ext_src_ks
    spin_taste_extend ${spin_taste_op}
    momentum #echo ' '.join(map(str,$momentum))#
    t0 ${tsrc}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,src,spin_taste_op,momentum,tsrc,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.src = src
        self.label = label
        self.spin_taste_op = spin_taste_op
        self.momentum = momentum
        self.tsrc = tsrc
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.src._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class ParallelTransportModSource:
    """Parallel-transported modified source."""
    _Template = """
    #== source ${id}: ${_classType} ==
    source ${startSource.id}
    par_xport_src_ks
    disp ${disp}
    #if $disp < 3 and $disp != 0:
    dir #echo ' '.join($dir)#
    #end if
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,startSource,disp,dir,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.startSource = startSource
        self.disp = disp
        self.dir = dir
        self.label = label
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        requires.append(self.startSource)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass
    ##if $disp == 1:
    #dir ${dir[0]}
    ##else if $disp == 2:
    #dir ${dir[0]} ${dir[1]}
    ##end if

class MomentumModSource:
    """Multiply source by a momentum phase over timeslice."""
    _Template = """
    #== source ${id}: ${_classType} ==
    source ${startSource.id}
    momentum
    momentum #echo ' '.join(map(str,$mom))#
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,startSource,mom,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.startSource = startSource
        self.mom = mom
        self.label = label
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        requires.append(self.startSource)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class RadialWavefunction:
    """Radial wavefunction source from a file. Either as a base or a derived source type."""
    _Template = """
    #== source ${id}: ${_classType} ==
    #if $startSource is not None:
    source ${startSource.id}
    #end if
    wavefunction
    #echo ' '.join($load)#
    #if $stride is not None:
    stride ${stride}
    #end if
    a ${afm}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,label,afm,stride,load,save,startSource=None):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.label = label
        self.afm = afm
        self.stride = stride
        self.load = load
        self.save = save
        self.startSource = startSource
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.load) > 1:
            requires.append(self.load[1])
            pass
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        if self.startSource is not None:
            depends.append(self.startSource._objectID)
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class FermilabRotation:
    """Apply a Fermilab rotation to a source."""
    _Template = """
    #== source ${id}: ${_classType} ==
    #if $startSource is not None:
    source ${startSource.id}
    #end if
    rotate_3D
    d1 ${d1}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,label,d1,save,startSource=None):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.label = label
        self.d1 = d1
        self.save = save
        self.startSource = startSource
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.load) > 1:
            requires.append(self.load[1])
            pass
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        if self.startSource is not None:
            depends.append(self.startSource._objectID)
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class CovariantGaussian:
    """Covariant Gaussian source from unsmeared links. Either as a base or a derived source type."""
    _Template = """
    #== source ${id}: ${_classType} ==
    #if $startSource is not None:
    source ${startSource.id}
    #end if
    fat_covariant_gaussian
    stride ${gparams.stride}
    r0 ${gparams.r0}
    source_iters ${gparams.iters}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,gparams,label,save,startSource=None):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.gparams = gparams
        self.label = label
        self.save = save
        self.startSource = startSource
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        if self.startSource is not None:
            depends.append(self.startSource._objectID)
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class FatCovariantGaussian:
    """Covariant Gaussian source from APE smeared links. Either as a base or a derived source type."""
    _Template = """
    #== source ${id}: ${_classType} ==
    #if $startSource is not None:
    source ${startSource.id}
    #end if
    fat_covariant_gaussian
    stride ${gparams.stride}
    r0 ${gparams.r0}
    source_iters ${gparams.iters}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,gparams,label,save,startSource=None):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.gparams = gparams
        self.label = label
        self.save = save
        self.startSource = startSource
        #try:
        # self.tsrc = startSource.tsrc
        #except AttributeError:
        # self.tsrc = startSource.origin[3]
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        if self.startSource is not None:
            depends.append(self.startSource._objectID)
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class FatCovariantLaplacian:
    """Covariant laplacian source from APE smeared links. Either as a base or a derived source type."""
    _Template = """
    #== source ${id}: ${_classType} ==
    #if $startSource is not None:
    source ${startSource.id}
    #end if
    fat_covariant_laplacian
    stride ${stride}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,stride,label,save,startSource=None):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.stride = stride
        self.label = label
        self.save = save
        self.startSource = startSource
        try:
         self.tsrc = startSource.tsrc
        except AttributeError:
         self.tsrc = startSource.origin[3]
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        if self.startSource is not None:
            depends.append(self.startSource._objectID)
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class FatCovariantGaussianSink:
    """Covariant Gaussian sink with APE-smeared links."""
    _Template = """
    #== quark ${id}: ${_classType} ==
    ${prop.type} ${prop.id}
    fat_covariant_gaussian
    stride ${gparams.stride}
    r0 ${gparams.r0}
    source_iters ${gparams.iters}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,prop,gparams,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop = prop
        self.gparams = gparams
        self.label = label
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.prop._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class FatCovariantLaplacianSink:
    """Covariant Laplacian sink with APE-smeared links."""
    _Template = """
    #== quark ${id}: ${_classType} ==
    ${prop.type} ${prop.id}
    fat_covariant_laplacian
    stride ${stride}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,prop,stride,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop = prop
        self.stride = stride
        self.label = label
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.prop._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class SolveKS:
    """su3_clov KS propagator solve."""
    _Template = """
    #== propagator ${id}: ${_classType} ==
    propagator_type KS
    mass ${mass}
    #if $naik_epsilon is not None:
    naik_term_epsilon ${naik_epsilon}
    #end if
    check ${check}
    error_for_propagator ${residual.L2}
    rel_error_for_propagator ${residual.R2}
    precision ${precision}
    momentum_twist #echo ' '.join(map(str,$twist))#
    source ${source.id}
    #echo ' '.join($load)#
    #echo ' '.join($save)#"""
    def __init__(self,mass,naik_epsilon,source,twist,bc,load,save,residual,precision,check):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.mass = mass
        self.naik_epsilon = naik_epsilon
        self.source = source
        self.twist = twist
        self.bc = bc
        self.load = load
        self.save =save
        self.residual = residual
        self.precision = precision
        self.check = check
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.load) > 1:
            requires.append(self.load[1])
            pass
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        depends.append(self.source._objectID)
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class SolveClover:
    """su3_clov Clover propagator solve."""
    _Template = """
    #== propagator ${id}: ${_classType} ==
    propagator_type clover
    kappa ${kappa}
    clov_c ${cSW}
    check ${check}
    error_for_propagator ${residual.L2}
    rel_error_for_propagator ${residual.R2}
    precision ${precision}
    momentum_twist #echo ' '.join(map(str,$twist))#
    time_bc ${bc}
    source ${source.id}
    #echo ' '.join($load)#
    #echo ' '.join($save)#"""
    def __init__(self,kappa,cSW,source,twist,bc,load,save,residual,precision,check):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.kappa = kappa
        self.cSW = cSW
        self.source = source
        self.twist = twist
        self.bc = bc
        self.load = load
        self.save =save
        self.residual = residual
        self.precision = precision
        self.check = check
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if len(self.load) > 1:
            requires.append(self.load[1])
            pass
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        depends.append(self.source._objectID)
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class GeneralSink8Container:
    """Container for applying a sink treatment to any octet of propagators.
       Takes an input function as an argument, which is applied to each source in the octet.
       Input function must have 3 arguments only: prop, label, save."""
    _Template="""
    #== source octet ${id}: ${_classType} ==
    octet $quark[0].id $quark[1].id $quark[2].id $quark[3].id $quark[4].id $quark[5].id $quark[6].id $quark[7].id"""
    def __init__(self,prop8,index,inputFn,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop8 = prop8
        self.quark = list()
        self.mass = prop8.mass[index]
        self.naik = prop8.naik[index]
        for i in range(8):
            prop = self.prop8.solveset[i].propagator[index]
            self.quark.append(inputFn(prop,
              NameFormatMass(NameFormatCube(label,vecStr[i]),self.mass),
              NameFormatMass(NameFormatCube(save,vecStr[i]),self.mass))) ## num->str
            pass
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
    def addQuarksToSpectrum(self,spect):
        for i in range(8):
            spect.addQuark(self.quark[i])
            pass
        return

class QuarkIdentitySink8Container:
    """Container for 8 QuarkIdentitySinks for corner walls."""
    """Uses KSsolveSet8Container for variable prop8 in place of single sources"""
    """Groups by masses; index indicates mass"""
    def __init__(self,prop8,index,label,save,multisource=False,multisrc_prop_idx=None):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.quark = list()
        self.index = index 
        self.mass = prop8.mass[index]
        self.naik = prop8.naik[index]
        for i in range(8):
            if not multisource:
                prop = prop8.solveset[i].propagator[index]
            else:
                # Multisource solves could contain multiple octets in one 
                # set of solves, multisrc_prop_idx indicates which one to apply 
                prop = prop8.solveset[0].propagator[multisrc_prop_idx*8+i] 
            self.quark.append(QuarkIdentitySink(prop,
            NameFormatMass(NameFormatCube(label,vecStr[i]),self.mass),
            NameFormatMass(NameFormatCube(save,vecStr[i]),self.mass))) ## num->str
            pass
    def addQuarksToSpectrum(self,spect):
        for i in range(8):
            spect.addQuark(self.quark[i])
            pass
        return

class SaveVectorSrc8Container:
    """Container for 8 SaveVectorSrc"""
    """Uses KSsolveSet8Container for variable prop8 in place of single sources"""
    """Groups by masses; index indicates mass"""
    def __init__(self,prop8,index,label,save_src,t0,
                 save_quark,multisource=False,multisrc_prop_idx=None):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.quark = list()
        self.index = index 
        self.mass = prop8.mass[index]
        self.naik = prop8.naik[index]
        for i in range(8):
            if not multisource:
                prop = prop8.solveset[i].propagator[index]
            else:
                # Multisource solves could contain multiple octets in one 
                # set of solves, multisrc_prop_idx indicates which one to apply 
                prop = prop8.solveset[0].propagator[multisrc_prop_idx*8+i] 
            self.quark.append(SaveVectorSrc(prop,
                NameFormatMass(NameFormatCube(label,vecStr[i]),self.mass),
                NameFormatMass(NameFormatCube(save_src,vecStr[i]),self.mass),t0,
                NameFormatMass(NameFormatCube(save_quark,vecStr[i]),self.mass))) 
            pass
    def addQuarksToSpectrum(self,spect):
        for i in range(8):
            spect.addQuark(self.quark[i])
            pass
        return

class QuarkModificationSink8Container:
    """Container for modifying propagator inversions in an octet container
       Uses KSsolveSet8Container for variable prop8 in place of single sources
       Groups by masses; index indicates mass
       Input function should have only three arguments: prop,label,save."""
    def __init__(self,prop8,inputfn,index,label,save,
                 multisource=False,multisrc_prop_idx=None):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.quark = list()
        self.index = index
        self.mass = prop8.mass[index]
        self.naik = prop8.naik[index]
        for i in range(8):
            if not multisource:
                prop = prop8.solveset[i].propagator[index]
            else:
                # Multisource solves could contain multiple octets in one 
                # set of solves, multisrc_prop_idx indicates which one to apply 
                prop = prop8.solveset[0].propagator[multisrc_prop_idx*8+i]  
            self.quark.append(inputfn(prop,
            NameFormatMass(NameFormatCube(label,vecStr[i]),self.mass),
            NameFormatMass(NameFormatCube(save,vecStr[i]),self.mass))) ## num->str
            pass

    def addQuarksToSpectrum(self,spect):
        for i in range(8):
            spect.addQuark(self.quark[i])
            pass
        return

class QuarkIdentitySink:
    """NOP fermion sink smearing."""
    ###if $quark8 is True:
    ##identity
    ##op_label ${label}
    ###end if
    _Template = """
    #== quark ${id}: ${_classType} ==
    ${prop.type} ${prop.id}
    identity
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,prop,label,save,quark8=False):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop = prop
        self.label = label
        self.save = save
        self.quark8 = quark8
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.prop._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class SaveVectorSrc:
    """
    Saving the quark as source
    """
    _Template = """
    #== quark ${id}: ${_classType} ==
    ${prop.type} ${prop.id}
    save_vector_src
    #echo ' '.join($save_src)#
    t0 ${t0}
    op_label ${label}
    #echo ' '.join($save_quark)#"""
    def __init__(self,prop,label,save_src,t0,save_quark,quark8=False):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop = prop
        self.save_src = save_src
        self.t0 = t0
        self.label = label
        self.save_quark = save_quark
        self.quark8 = quark8
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    pass


class KSQuarkOctet:
    """Consolidates 8 ks quarks into an octet for use in Golterman-Bailey Baryon spectra"""
    """Uses some grouping of 8 quarks similar to QuarkIdentitySink8Container"""
    """ for variable qk8 in place of single sources"""
    """Need to indicate that it is intended as a strange quark where appropriate"""
    _Template = """
    #== octet ${id}: ${_classType} ==
    octet $qk8.quark[0].id $qk8.quark[1].id $qk8.quark[2].id $qk8.quark[3].id $qk8.quark[4].id $qk8.quark[5].id $qk8.quark[6].id $qk8.quark[7].id"""
    def __init__(self,qk8):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.qk8 = qk8
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        for i in range(8):
            depends.append(self.qk8.quark[i]._objectID)
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class RadialWavefunctionSink:
    """Smear fermion sink with a radial wavefunction input from file."""
    _Template = """
    #== quark ${id}: ${_classType} ==
    ${prop.type} ${prop.id}
    wavefunction
    #echo ' '.join($load)#
    #if $stride is not None:
    stride ${stride}
    #end if
    a ${afm}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,prop,label,afm,stride,load,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop = prop
        self.label = label
        self.afm = afm
        self.stride = stride
        self.load = load
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.prop._objectID)
        if len(self.load) > 1:
            requires.append(self.load[1])
            pass
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class FermilabRotateSink:
    """Apply a Fermilab rotation to a propagator."""
    _Template = """
    #== quark ${id}: ${_classType} ==
    ${prop.type} ${prop.id}
    rotate_3D
    d1 ${d1}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,prop,label,d1,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop = prop
        self.label = label
        self.d1 = d1
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.prop._objectID)
        if len(self.load) > 1:
            requires.append(self.load[1])
            pass
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class DiracExtSrcSink:
    """Restrict Dirac fermion propagator to time slice."""
    _Template = """
    #== quark ${id}: ${_classType} ==
    ${prop.type} ${prop.id}
    ext_src_dirac
    gamma ${gamma}
    momentum #echo ' '.join(map(str,$momentum))#
    t0 ${time_slice}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,prop,gamma,momentum,time_slice,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop = prop
        self.label = label
        self.gamma = gamma
        self.momentum = momentum
        self.time_slice = time_slice
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.prop._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class KSExtSrcSink:
    """Restrict KS fermion propagator to time slice."""
    _Template = """
    #== quark ${id}: ${_classType} ==
    ${prop.type} ${prop.id}
    ext_src_ks
    spin_taste_extend ${spin_taste_op}
    momentum #echo ' '.join(map(str,$momentum))#
    t0 ${time_slice}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,prop,spin_taste_op,momentum,time_slice,subset,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop = prop
        self.label = label
        self.spin_taste_op = spin_taste_op
        self.momentum = momentum
        self.time_slice = time_slice
        self.subset = subset
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.prop._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class KSExtSrcSink8Container:
    """Container of eight extended source sink operators."""
    #_Template = """
    ##== quark ${id}: ${_classType} ==
    #${prop.type} ${prop.id}
    #ext_src_ks
    #spin_taste ${spin_taste_op}
    #momentum #echo ' '.join(map(str,$momentum))#
    #t0 ${time_slice}
    #op_label ${label}
    ##echo ' '.join($save)#"""
    def __init__(self,prop8,spin_taste_op,momentum,time_slice,subset,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop8 = prop8
        self.quark = list()
        self.mass = prop8.mass
        self.label = label
        self.spin_taste_op = spin_taste_op
        self.momentum = momentum
        self.time_slice = time_slice
        self.subset = subset
        self.save = save
        try:
         iter8 = self.prop8.quark
        except AttributeError:
         iter8 = self.prop8.solveset[0]
        for i,prop in enumerate(iter8):
            self.quark.append(
             KSExtSrcSink(prop,self.spin_taste_op,self.momentum,self.time_slice,self.subset,
              NameFormatMass(NameFormatCube(self.label,vecStr[i]),self.mass),
              NameFormatMass(NameFormatCube(self.save,vecStr[i]),self.mass)))
            pass
        #self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def addQuarksToSpectrum(self,spect):
        for qk in self.quark:
           spect.addQuark(qk)
        ##for i in range(8):
        #try:
        # iter8 = self.prop8.quark
        #except AttributeError:
        # iter8 = self.prop8.solveset[0]
        #for i,prop in enumerate(iter8):
        #    spect.addQuark(
        #     KSExtSrcSink(prop,self.spin_taste_op,self.momentum,self.time_slice,self.subset,
        #      NameFormatMass(NameFormatCube(self.label,vecStr[i]),self.mass),
        #      NameFormatMass(NameFormatCube(self.save,vecStr[i]),self.mass)))
        #    pass
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.prop._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class KSInverseSink:
    """Extended KS inverse sink operator."""
    _Template = """
    #== quark ${id}: ${_classType} ==
    ${prop.type} ${prop.id}
    ks_inverse
    mass ${mass}
    #if $naik_epsilon is not None:
    naik_term_epsilon ${naik_epsilon}
    #end if
    u0 ${u0}
    max_cg_iterations ${maxCG.iters}
    max_cg_restarts ${maxCG.restarts}
    deflate no
    error_for_propagator ${residual.L2}
    rel_error_for_propagator ${residual.R2}
    precision ${precision}
    momentum_twist #echo ' '.join(map(str,$twist))#
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,prop,mass,naik_epsilon,u0,maxCG,residual,precision,origin,twist,bc,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop = prop
        self.label = label
        self.mass = mass
        self.naik_epsilon = naik_epsilon
        self.u0 = u0
        self.maxCG = maxCG
        self.residual = residual
        self.precision = precision
        self.origin = origin
        self.twist = twist
        self.bc = bc
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.prop._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class KSInverseSink8Container:
    """An octet of extended KS inverse sink operators."""
    def __init__(self,prop8,mass,naik_epsilon,u0,maxCG,residual,precision,origin,twist,bc,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop8 = prop8
        self.quark = list()
        self.label = label
        self.mass = mass
        self.naik_epsilon = naik_epsilon
        self.u0 = u0
        self.maxCG = maxCG
        self.residual = residual
        self.precision = precision
        self.origin = origin
        self.twist = twist
        self.bc = bc
        self.save = save
        try:
          iter8 = prop8.quark
        except AttributeError:
          iter8 = prop8.prop
        for i,prop in enumerate(iter8):
          self.quark.append(KSInverseSink(\
            prop,mass,naik_epsilon,u0,maxCG,residual,precision,origin,twist,bc,\
            NameFormatCube(label,vecStr[i]),NameFormatCube(save,vecStr[i])))
        return
    def addQuarksToSpectrum(self,spect):
        for qk in self.quark:
          spect.addQuark(qk)
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.prop8._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class DiracInverseSink:
    """Extended Dirac inverse sink operator."""
    _Template = """
    #== quark ${id}: ${_classType} ==
    ${prop.type} ${prop.id}
    dirac_inverse
    kappa ${kappa}
    clov_c ${clov_c}
    u0 ${u0}
    max_cg_iterations ${maxCG.iters}
    max_cg_restarts ${maxCG.restarts}
    error_for_propagator ${residual.L2}
    rel_error_for_propagator ${residual.R2}
    precision ${precision}
    coordinate_origin #echo ' '.join(map(str,$origin))#
    momentum_twist #echo ' '.join(map(str,$twist))#
    time_bc ${bc}
    op_label ${label}
    #echo ' '.join($save)#"""
    def __init__(self,prop,kappa,clov_c,u0,maxCG,residual,precision,origin,twist,bc,label,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prop = prop
        self.label = label
        self.kappa = kappa
        self.clov_c = clov_c
        self.u0 = u0
        self.maxCG = maxCG
        self.residual = residual
        self.precision = precision
        self.origin = origin
        self.twist = twist
        self.bc = bc
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.prop._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class MesonSpectrum:
    """Meson spectrum specification."""
    _Template = """
    #== ${_classType} ==
    pair ${antiQuark.id} ${quark.id}
    spectrum_request meson
    #echo ' '.join($save)#
    r_offset #echo ' '.join(map(str,$relOffset))#
    number_of_correlators #echo len($npts)"""
    def __init__(self,antiQuark,quark,relOffset,npts,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.antiQuark = antiQuark
        self.quark = quark
        self.relOffset = relOffset
        self.npts = npts
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        for c in self.npts:
            c.generate(ostream)
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.antiQuark._objectID)
        depends.append(self.quark._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class MesonNpt:
    """A meson n-point function."""
    _Template = """correlator ${prefix} ${postfix} #echo ' '.join(map(str,$norm))# #echo ' '.join($gamma)# #echo ' '.join(map(str,$momentum))# #echo ' '.join($parity)"""
    def __init__(self,prefix,postfix,norm,gamma,momentum,parity):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prefix = prefix
        self.postfix = postfix
        self.norm = norm
        self.gamma = gamma
        self.momentum = momentum
        self.parity = parity
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return

class BaryonSpectrum:
    """Baryon spectrum specification."""
    """MILC's standard baryon spectrum object."""
    _Template = """
    #== ${_classType} ==
    triplet $qi.id $qj.id $qk.id
    spectrum_request baryon
    #echo ' '.join($save)#
    r_offset #echo ' '.join(map(str,$relOffset))#
    number_of_correlators #echo len($nbcor)#
    """
    def __init__(self,qi,qj,qk,nbcor,relOffset,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.qi = qi
        self.qj = qj
        self.qk = qk
        self.nbcor = nbcor
        self.relOffset = relOffset
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        for c in self.nbcor:
            c.generate(ostream)
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.qi._objectID)
        depends.append(self.qj._objectID)
        depends.append(self.qk._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class Baryon2pt:
    """A generic MILC baryon 2-point function."""
    _Template = """correlator ${label} #echo ' '.join(map(str,$norm))# ${req}
    """
    def __init__(self,label,norm,isNucleon):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.label = label
        self.norm = norm
        if isNucleon:
          self.req = 'nucleon'
        else:
          self.req = 'delta'
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return

class RuiziBaryonSpectrum:
    """(Ruizi) Baryon spectrum specification."""
    """Only supports calculation of all baryons (unknown syntax for others)"""
    _Template = """
    #== ${_classType} ==
    num_triplet 24
    lqmass 4
    baryon_index $index
    triplet $qi[0].id $qi[1].id $qi[2].id $qi[3].id $qj[0].id $qj[1].id $qj[2].id $qj[3].id\
 $qk[0].id $qk[1].id $qk[2].id $qk[3].id $qi[4].id $qi[5].id $qi[6].id $qi[7].id\
 $qj[4].id $qj[5].id $qj[6].id $qj[7].id $qk[4].id $qk[5].id $qk[6].id $qk[7].id
    spectrum_request baryon
    #echo ' '.join($save)#
    r_offset #echo ' '.join(map(str,$relOffset))#
    number_of_correlators 1
    correlator ALL 1 * 1 all"""
    def __init__(self,quark8i,quark8j,quark8k,index,relOffset,save):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.qi = self.sortQuarks(quark8i)
        self.qj = self.sortQuarks(quark8j)
        self.qk = self.sortQuarks(quark8k)
        self.index = index
        self.relOffset = relOffset
        self.save = save
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def sortQuarks(self,quark8):
        """Reorder single quarks to fit Ruizi convention"""
        qsort = list()
        qsort.append(quark8.quark[0])
        qsort.append(quark8.quark[4])
        qsort.append(quark8.quark[2])
        qsort.append(quark8.quark[1])
        qsort.append(quark8.quark[6])
        qsort.append(quark8.quark[3])
        qsort.append(quark8.quark[5])
        qsort.append(quark8.quark[7])
        return qsort
    def unsortQuarks(self,quark8):
        """Reorder single quarks to fit Ruizi convention"""
        return [quark8[i] for i in [0,3,2,5,1,6,4,7]]
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        ## -- attempt to order them
        for i in range(8):
            depends.append(self.unsortQuarks(self.qi)[i]._objectID)
        for i in range(8):
            depends.append(self.unsortQuarks(self.qj)[i]._objectID)
        for i in range(8):
            depends.append(self.unsortQuarks(self.qk)[i]._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class GBBaryonSpectrum:
    """Golterman-Bailey Baryon spectrum specification."""
    """  """
    _Template = """
    #== ${_classType} ==
    triplet $octeti.id $octetj.id $octetk.id
    spectrum_request gb_baryon
    quark_content $cont
    #echo ' '.join($save)#
    r_offset #echo ' '.join(map(str,$relOffset))#
    #if $mom is not None
    momentum #echo ' '.join(map(str,$mom))# #echo ' '.join($par)#
    #end if
    #if $stidx is not None
    spin_taste ${stidx}
    #else
    spin_taste 2point
    #end if
    number_of_correlators #echo len($nbcor)#"""
    def __init__(self,octeti,octetj,octetk,relOffset,nbcor,cont,save,mom=None,par=None,stidx=None):
        ## optional argument for compatibility reasons
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.octeti = octeti
        self.octetj = octetj
        self.octetk = octetk
        self.str = len(cont.split('s'))-1
        self.relOffset = relOffset
        self.nbcor = nbcor
        self.cont = cont
        self.save = save
        self.mom = mom
        self.stidx = stidx
        self.par = par
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        for c in self.nbcor:
            c.generate(ostream)
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.octeti._objectID)
        depends.append(self.octetj._objectID)
        depends.append(self.octetk._objectID)
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class GBBaryon2pt:
    """A Golterman-Bailey baryon 2-point function."""
    _Template = """correlator ${prefix} #echo ' '.join(map(str,$norm))# $gtsc $si_src $src $gtsk $si_snk $snk $snkdisp $snktie $corner"""
    #def __init__(self,prefix,norm,gts,si_src,src,si_snk,snk,corner=None):
    def __init__(self,prefix,norm,gtsc,si_src,src,gtsk,si_snk,snk,snkdisp,snktie,corner):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.prefix = prefix
        #self.postfix = postfix
        self.norm = norm
        self.gtsc = gtsc
        self.gtsk = gtsk
        self.si_src = si_src
        self.si_snk = si_snk
        self.src = src
        self.snk = snk
        self.snkdisp = snkdisp
        self.snktie = snktie
        if not(corner is None):
         self.corner = corner
        else:
         self.corner = ''
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return

class GBBaryon3ptFunction:
    """A Golterman-Bailey baryon 3-point function object."""
    _Template = """
    #== ${_classType} ${id} ==
    triplet $octeti.id $octetj.id $octetk.id
    spectrum_request gb_baryon_3pt
    source_quark_content ${srcCont}
    sink_quark_content ${snkCont}
    source_time ${tsrc}
    r_offset #echo ' '.join(map(str,$relOffset))#
    file_prefix $fpre
    file_delim $fdel
    file_suffix $fsuf
    """
    def __init__(self,label,octeti,octetj,octetk,srcCont,snkCont,tsrc,relOffset,fpre,fdel,fsuf):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.label = label
        self.octeti = octeti
        self.octetj = octetj
        self.octetk = octetk
        self.srcCont = srcCont
        self.snkCont = snkCont
        self.relOffset = relOffset
        self.tsrc = tsrc
        self.fpre = fpre
        self.fdel = fdel
        self.fsuf = fsuf
        self.sinkTimeslice = list()
        self.momentumList = list()
        self.correlatorList = list()
        self.currentList = list()
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def addSinkTimeslice(self,corr):
        self.sinkTimeslice.append(corr)
        return
    def addMomentum(self,corr):
        self.momentumList.append(corr)
        return
    def addCorrelator(self,corr):
        self.correlatorList.append(corr)
        return
    def addCurrent(self,curr):
        self.currentList.append(curr)
        return
    def generate(self,ostream):
        print>>ostream, self._template
        print>>ostream, 'number_of_sink_specifications', len(self.sinkTimeslice)
        for x in self.sinkTimeslice:
            x.generate(ostream)
            pass
        print>>ostream, 'number_of_momenta', len(self.momentumList)
        for x in self.momentumList:
            x.generate(ostream)
            pass
        print>>ostream, 'number_of_3pt_correlators', len(self.correlatorList)
        for x in self.correlatorList:
            x.generate(ostream)
            pass
        print>>ostream, 'number_of_current_insertions', len(self.currentList)
        for x in self.currentList:
            x.generate(ostream)
            pass
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.octeti._objectID)
        depends.append(self.octetj._objectID)
        depends.append(self.octetk._objectID)
        for x in self.sinkTimeslice:
            df = x.dataflow()
            for y in df['depends']:
                depends.append(y)
                pass
            for y in df['requires']:
                requires.append(y)
                pass
            for y in df['produces']:
                produces.append(y)
                pass
        #if len(self.save) > 1:
        #    produces.append(self.save[1])
        #    pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class GBBaryon3ptSinkTimeSlice:
    """A Golterman-Bailey baryon 3-point sink timeslice/momentum specification object."""
    _Template = """sink_specification $flabel $label $scOctet.id $qkOctet.id $tsnk $treverse"""
    def __init__(self,flabel,label,scOctet,qkOctet,tsnk,treverse):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.flabel = flabel
        self.label = label
        self.scOctet = scOctet
        self.qkOctet = qkOctet
        self.tsnk = tsnk
        if treverse == "yes+" or treverse == "yes-" or treverse == "no":
          self.treverse = treverse
        else:
          print "invalid time reversal string!"
          raise ValueError
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        if self.scOctet is not None:
            depends.append(self.scOctet._objectID)
        depends.append(self.qkOctet._objectID)
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class GBBaryon3ptMomentum:
    """A Golterman-Bailey baryon 3-point sink timeslice/momentum specification object."""
    _Template = """
    mom_file_label ${flabel}
    mom_sink $klabel #echo ' '.join(map(str,$msnk))# #echo ' '.join(map(str,$psnk))#
    mom_insertion $ilabel #echo ' '.join(map(str,$mins))# #echo ' '.join(map(str,$pins))#"""
    ##== ${_classType} ${id} ==
    #mom_sink $klabel $msnk[0] $msnk[1] $msnk[2] $psnk[0] $psnk[1] $psnk[2]
    #mom_insertion $ilabel $mins[0] $mins[1] $mins[2] $pins[0] $pins[1] $pins[2]
    def __init__(self,flabel,klabel,ilabel,msnk,mins,psnk,pins):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.flabel = flabel
        self.klabel = klabel
        self.ilabel = ilabel
        self.msnk = msnk
        self.mins = mins
        self.psnk = psnk
        self.pins = pins
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class GBBaryon3ptCorrelator:
    """A Golterman-Bailey baryon 3-point correlation function specification object."""
    #_Template = """correlator ${label} ${srcGts} ${srcSymIso} ${srcCls} ${snkGts} ${snkSymIso} ${snkCls} #echo ' '.join(map(str,$norm))#"""
    _Template = """correlator ${label} ${srcGts} ${srcSymIso} ${srcCls} ${snkGts} ${snkSymIso} ${snkCls} #echo ' '.join(map(str,$norm))# ${corner}"""
    def __init__(self,label,srcGts,srcSymIso,srcCls,snkGts,snkSymIso,snkCls,norm,corner=None):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.label = label
        self.srcGts = srcGts
        self.srcSymIso = srcSymIso
        self.srcCls = srcCls
        self.snkGts = snkGts
        self.snkSymIso = snkSymIso
        self.snkCls = snkCls
        self.norm = norm
        if not(corner is None):
         self.corner = corner
        else:
         self.corner = ''
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return

class GBBaryon3ptCurrent:
    """A Golterman-Bailey baryon 3-point current insertion object."""
    _Template = """current ${label} ${spinTaste} ${phase}"""
    def __init__(self,label,spinTaste,phase):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.label = label
        self.spinTaste = spinTaste
        self.phase = phase
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return

class _Cycle_su3_clov:
    def __init__(self):
        self.gauge = None
        self.maxIters = None
        self.maxRestarts = None
        self.bsource = list()
        self.msource = list()
        self.propagator = list()
        self.quark = list()
        self.spectrum = list()
        return
    def generate(self,ostream):
        self.gauge.generate(ostream)
        print>>ostream, 'max_cg_iterations', self.maxIters
        print>>ostream, 'max_cg_restarts', self.maxRestarts
        print>>ostream
        print>>ostream, '########### base sources ###############'
        print>>ostream
        print>>ostream, 'number_of_base_sources', len(self.bsource)
        for x in self.bsource:
            x.generate(ostream)
            pass
        print>>ostream
        print>>ostream, '########### modified sources ###############'
        print>>ostream
        print>>ostream, 'number_of_modified_sources', len(self.msource)
        for x in self.msource:
            x.generate(ostream)
            pass
        print>>ostream
        print>>ostream, '########### propagators ###############'
        print>>ostream
        print>>ostream, 'number_of_propagators', len(self.propagator)
        for x in self.propagator:
            x.generate(ostream)
        print>>ostream
        print>>ostream, '########### quarks ###############'
        print>>ostream
        print>>ostream, 'number_of_quarks', len(self.quark)
        for x in self.quark:
            x.generate(ostream)
            pass
        print>>ostream
        print>>ostream, '########### mesons ###############'
        print>>ostream
        print>>ostream, 'number_of_pairings', len(self.spectrum)
        for x in self.spectrum:
            x.generate(ostream)
        return
    def dataflow(self):
        dinfo = list()
        dinfo.append(self.gauge.dataflow())
        for x in self.bsource:
            dinfo.append(x.dataflow())
            pass
        for x in self.msource:
            dinfo.append(x.dataflow())
            pass
        for x in self.propagator:
            dinfo.append(x.dataflow())
            pass
        for x in self.quark:
            dinfo.append(x.dataflow())
            pass
        for x in self.spectrum:
            dinfo.append(x.dataflow())
            pass
        return dinfo
    pass

class su3_clov:
    """
    The MILC/su3_clov application.

    :Parameters:
      - `participantName`: A unique label for the workflow.
      - `dim`: List of lattice dimensions, [nX, nY, nZ, nT].
      - `seed`: Random number generator seed, use seed='None' to skip.
      - `jobID`: A unique identifier string used for data provenance, usually set to PBS_JOBID.
      - `layout`: The SciDAC node and io layout = { node: [Lx, Ly, Lz, Lt], io: [Ix, Iy, Iz, It] }. Use layout = 'None' to skip.
      - `prompt`: Echo MILC prompts to stdout (=0), no echo (=1) or check input validity (=2).

    The 'su3_clov' application is a pipline:

    - initialize lattice size, rng.seed
    - loop:
        - initialize gauge field
        - gauge fix
        - fat link APE smear
        - define base sources
        - define derived sources
        - define propagator solves
        - define quarks (propagator sink treatments)
        - spectroscopy: n-point tie-ups

    """
    def __init__(self,participantName,dim,seed,jobID,layout=None,prompt=0):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.pName = participantName
        self.geometry = Geometry(dim,seed,jobID,prompt,layout)
        self.requires = list()
        self.produces = list()
        self.cycle = [ ]
        self.cycnt = -1
        return
    def newGauge(self,uspec):
        """Add the gauge definition."""
        self.cycle.append(_Cycle_su3_clov())
        self.cycnt += 1
        self.cycle[self.cycnt].gauge = uspec
        return uspec
    def setCGparams(self,maxIters,maxRestarts):
        """Specify CG maximum restarts and iterations between restarts."""
        self.cycle[self.cycnt].maxIters = maxIters
        self.cycle[self.cycnt].maxRestarts = maxRestarts
        return
    def addBaseSource(self,src):
        """Add a base source specification"""
        self.cycle[self.cycnt].bsource.append(src)
        return src
    def addModSource(self,src):
        """Add a source derived from one of the base sources"""
        self.cycle[self.cycnt].msource.append(src)
        return src
    def addProp(self,prop):
        """Add a propagator solve."""
        prop.type = 'propagator'
        self.cycle[self.cycnt].propagator.append(prop)
        return prop
    def addQuark(self,quark):
        """Add a sink treatment to a propagator."""
        quark.type = 'quark'
        self.cycle[self.cycnt].quark.append(quark)
        return quark
    def addSpectrum(self,spect):
        """Add a spectrum specification that depends upon pairs of quarks."""
        self.cycle[self.cycnt].spectrum.append(spect)
        return spect
    def _bind_indices(self):
        """Bind indices to sources, propagators and quarks."""
        for cy in self.cycle:
            nbs = len(cy.bsource)
            for idx, s in zip(range(nbs),cy.bsource):
                s.id = idx
                pass
            nms = len(cy.msource)
            for idx, s in zip(range(nbs,nbs+nms),cy.msource):
                s.id = idx
                pass
            for idx, p in zip(range(len(cy.propagator)),cy.propagator):
                p.id = idx
                pass
            for idx, q in zip(range(len(cy.quark)),cy.quark):
                q.id = idx
                pass
        return
    def generate(self,ostream=sys.stdout):
        """Write MILC prompts to output stream 'ostream'."""
        self._bind_indices()
        self.geometry.generate(ostream)
        for x in self.cycle:
            x.generate(ostream)
            pass
        return
    def dataflow(self):
        self._bind_indices()
        w = list()
        for x in self.cycle:
            w.append(x.dataflow())
            pass
        dinfo = { 'title': self.pName, 'workflow': w }
        return dinfo
    pass

#----
class KSsolveSetNContainer_MultiSource:
    """Container for Arbitrary number of octet for multisource"""
    """Container for 8 KSsolveSets for octets."""
    """Uses CornerWall8Container or VectorSource8Container
       for variable source8 in place of single sources"""
    def __init__(self,twist,bc,check,maxCG,precision,
                 mass,naik_epsilon,residuals):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.source8List = list() # list of sources in octets
        self.twist = twist
        self.bc = bc 
        self.check = check
        self.maxCG = maxCG
        self.precision = precision
        self.residuals = residuals
        self.mass = mass
        self.naik = naik_epsilon
        self.nmass = len(mass)
        self.solveset = [KSsolveSet_MultiSource(
                        self.twist,self.bc,self.check,
                        self.maxCG,self.precision,
                        self.mass[0], self.naik[0])] # only one set


    def appendSolveSet(self,src8,load,save):
        """
        Append more solves to a single set of solvers for multisource
        """
        self.source8List.append(src8)
        nSrc = len(src8.source)
        for iciter in range(8):
            loadt = NameFormatCube(load,vecStr[iciter])
            savet = NameFormatCube(save,vecStr[iciter])
            loadformat = NameFormatMass(loadt,self.mass[0])
            saveformat = NameFormatMass(savet,self.mass[0])
            if(iciter < nSrc):
                isrc = src8.source[iciter]
            else:
                isrc = src8.modifd[iciter-nSrc]
            prop = KSsolveElement_MultiSource(
                    isrc,loadformat,saveformat,self.residuals)
            self.solveset[0].addPropagator(prop) # only one set 
        
    def addSolvesToSpectrum(self,spect):
        spect.addPropSet(self.solveset[0]) # only one set
        return

class KSsolveSet8Container:
    """Container for 8 KSsolveSets for octets."""
    """Uses CornerWall8Container or VectorSource8Container
       for variable source8 in place of single sources"""
    def __init__(self,source8,twist,bc,check,maxCG,precision,
                 mass,naik_epsilon,load,save,residuals):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.solveset = list()
        self.source8 = source8
        self.twist = twist
        self.bc = bc 
        self.check = check
        self.maxCG = maxCG
        self.precision = precision
        self.residuals = residuals
        self.mass = mass
        self.naik = naik_epsilon
        self.nmass = len(mass)
        self.nSrc = len(source8.source)

        for i in range(8):
            if(i < self.nSrc):
                ## CornerWall8Container and VectorSource8Container
                self.solveset.append(KSsolveSet(source8.source[i],
                    twist,bc,check,maxCG,precision))
            else:
                ## VectorSource8Container / GeneralSource8Container
                self.solveset.append(KSsolveSet(source8.modifd[i-self.nSrc],
                    twist,bc,check,maxCG,precision))
                pass
            loadt = NameFormatCube(load,vecStr[i])
            savet = NameFormatCube(save,vecStr[i])
            for m, nk in zip(mass,naik_epsilon):
                prop = KSsolveElement(m,nk,
                NameFormatMass(loadt,m),
                NameFormatMass(savet,m),residuals)
                self.solveset[i].addPropagator(prop)
                pass
            pass
        
    def addSolvesToSpectrum(self,spect):
        for i in range(8):
            spect.addPropSet(self.solveset[i])

class KSsolveSet:
    """A set of KS solves that have a common source specification, momentum twist, BC and precision."""
    _Template = """
    #== ${_classType} ==
    max_cg_iterations ${maxCG.iters}
    max_cg_restarts ${maxCG.restarts}
    check ${check}
    momentum_twist #echo ' '.join(map(str,$twist))#
    precision ${precision}
    source ${source.id}"""
    def __init__(self,source,twist,bc,check,maxCG,precision):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.source = source
        self.twist = twist
        self.bc = bc
        self.check = check
        self.maxCG = maxCG
        self.precision = precision
        self.propagator = list()
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    # container behavior
    def __len__(self):
        return len(self.propagator)
    def __iter__(self):
        return self.propagator.__iter__()
    def __add__(self,other):
        return [ x for x in self.propagator+other.propagator ]
    def addPropagator(self,prop):
        """Add a KSsolveElement object to the set of solves."""
        prop.parent = self
        prop.type = 'propagator'
        self.propagator.append(prop)
        return prop
    def generate(self,ostream):
        print>>ostream, self._template
        print>>ostream, 'number_of_propagators', len(self.propagator)
        for p in self.propagator:
            p.generate(ostream)
            pass
        return
    def dataflow(self):
        df = list()
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.source._objectID)
        df.append( { 'name': wname, 'depends': depends,
                     'requires': requires, 'produces': produces } )
        for p in self.propagator:
            df.append(p.dataflow())
            pass
        return df
    pass

class KSsolveElement:
    """Specification of a single KS solve in a KSsolveSet."""
    _Template = """
    #== propagator ${id}: ${_classType} ==
    mass ${mass}
    #if $naik is not None
    naik_term_epsilon ${naik}
    #end if
    error_for_propagator ${residual.L2}
    rel_error_for_propagator ${residual.R2}
    #echo ' '.join($load)#
    #echo ' '.join($save)#
    """
    def __init__(self,mass,naik,load,save,residual):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.id = None
        self.parent = None # the KSsolveSet
        self.mass = mass
        self.naik = naik
        self.load = load
        self.save = save
        self.residual = residual
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.parent._objectID)
        if len(self.load) > 1:
            requires.append(self.load[1])
            pass
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass


class KSsolveSet_MultiSource:
    """A set of KS solves that have a common momentum twist, BC and precision with multisources."""
    _Template = """
    #== ${_classType} ==
    set_type multisource
    max_cg_iterations ${maxCG.iters}
    max_cg_restarts ${maxCG.restarts}
    check ${check}
    momentum_twist #echo ' '.join(map(str,$twist))#
    precision ${precision}
    mass ${mass}
    #if $naik is not None
    naik_term_epsilon ${naik}
    #end if
    """
    def __init__(self,twist,bc,check,maxCG,precision,mass,naik):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.twist = twist
        self.bc = bc
        self.check = check
        self.maxCG = maxCG
        self.precision = precision
        self.mass = mass
        self.naik = naik
        self.propagator = list()
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    # container behavior
    def __len__(self):
        return len(self.propagator)
    def __iter__(self):
        return self.propagator.__iter__()
    def __add__(self,other):
        return [ x for x in self.propagator+other.propagator ]
    def addPropagator(self,prop):
        """Add a KSsolveElement_MultiSource object to the set of solves."""
        prop.parent = self
        prop.type = 'propagator'
        self.propagator.append(prop)
        return prop
    def generate(self,ostream):
        print>>ostream, self._template
        print>>ostream, 'number_of_propagators', len(self.propagator)
        for p in self.propagator:
            p.generate(ostream)
            pass
        return
    def dataflow(self):
        df = list()
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        df.append( { 'name': wname, 'depends': depends,
                     'requires': requires, 'produces': produces } )
        for p in self.propagator:
            df.append(p.dataflow())
            pass
        return df
    pass

class KSsolveElement_MultiSource:
    """Specification of a single KS solve in a KSsolveSet_MultiSource."""
    _Template = """
    #== propagator ${id}: ${_classType} ==
    source ${source.id}
    error_for_propagator ${residual.L2}
    rel_error_for_propagator ${residual.R2}
    #echo ' '.join($load)#
    #echo ' '.join($save)#
    """
    def __init__(self,source,load,save,residual):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.id = None
        self.parent = None # the KSsolveSet_MultiSource
        self.source = source
        self.load = load
        self.save = save
        self.residual = residual
        self._template = Template(source=textwrap.dedent(self._Template),searchList=vars(self))
        return
    def generate(self,ostream):
        print>>ostream, self._template
        return
    def dataflow(self):
        wname = self._objectID
        depends = list()
        requires = list()
        produces = list()
        depends.append(self.parent._objectID)
        if len(self.load) > 1:
            requires.append(self.load[1])
            pass
        if len(self.save) > 1:
            produces.append(self.save[1])
            pass
        return { 'name': wname, 'depends': depends,
                 'requires': requires, 'produces': produces }
    pass

class ks_spectrum:
    """
    MILC application MILC/ks_spectrum application.
    The milc applications are designed as pipelines.
    The ks_spectrum pipline:

    - initialize lattice size, rng
    - loop:
        - init gauge field
        -  gauge fix
        -  link smear
        -  pbp masses??
        -  define sources
        -  define KS propsets
        -  define quarks (sink treatments)
        -  meson spectroscopy
        -  baryon spectroscopy
        -  group quark octets
        -  golterman-bailey baryon spectroscopy

    """
    def __init__(self,participantName,dim,seed,jobID,layout=None,prompt=0):
        self._classType = self.__class__.__name__
        self._objectID = self._classType+'_'+base36(id(self))
        self.pName = participantName
        self.geometry = Geometry(dim,seed,jobID,prompt,layout)
        self.requires = list()
        self.produces = list()
        self.cycle = [ ]
        self.cycnt = -1
        return
    def newGauge(self,uspec):
        """Add a gauge field specification."""
        self.cycle.append(_Cycle_ks_spectrum())
        self.cycnt += 1
        self.cycle[self.cycnt].gauge = uspec
        return uspec
    def addBaseSource(self,src):
        """Add a base source specification."""
        self.cycle[self.cycnt].bsource.append(src)
        return src
    def addModSource(self,src):
        """Add a modified source dependent upon one of the base sources."""
        self.cycle[self.cycnt].msource.append(src)
        return src
    def addPropSet(self,pset):
        """Add a KSsolveSet object."""
        self.cycle[self.cycnt].pset.append(pset)
        return pset
    def addQuark(self,quark):
        """Add a propagator sink treatment (a quark) to the workflow. The quark depends upon an KSsolveElement object."""
        quark.type = 'quark'
        self.cycle[self.cycnt].quark.append(quark)
        return quark
    def addMeson(self,meson):
        """Add meson spectroscopy."""
        self.cycle[self.cycnt].meson.append(meson)
        return meson
    def addBaryon(self,baryon):
        """Add baryon spectroscopy (implemented for ruizi or generic MILC, NOT BOTH)."""
        self.cycle[self.cycnt].baryon.append(baryon)
        return baryon
    def addSourceOctet(self,scoctet):
        """Add octet of sources."""
        self.cycle[self.cycnt].scoctet.append(scoctet)
        return scoctet
    def addQuarkOctet(self,qkoctet):
        """Add octet of quarks."""
        self.cycle[self.cycnt].qkoctet.append(qkoctet)
        return qkoctet
    def addGBBaryon(self,gbbaryon):
        """Add Golterman-Bailey baryon spectroscopy"""
        self.cycle[self.cycnt].gbbaryon.append(gbbaryon)
        return gbbaryon
    def addGB3Point(self,gb3pt):
        """Add Golterman-Bailey baryon 3-point function"""
        self.cycle[self.cycnt].gb3pt.append(gb3pt)
        return gb3pt
    def GB3PointOn(self):
        """Turn on 3-point structure even without GB 3-point functions defined"""
        self.cycle[self.cycnt].gb3ptOn = True
        return
    def _bind_indices(self):
        """Bind indices to sources, propagators, quarks, octets, and 3-points."""
        for cy in self.cycle:
            nbs = len(cy.bsource)
            for idx, s in zip(range(nbs),cy.bsource):
                s.id = idx
                pass
            nms = len(cy.msource)
            for idx, s in zip(range(nbs,nbs+nms),cy.msource):
                s.id = idx
                pass
            idx = 0
            for ps in cy.pset:
                for p in ps:
                    p.id = idx
                    idx += 1
                    pass
                pass
            for idx, q in zip(range(len(cy.quark)),cy.quark):
                q.id = idx
                pass
            for idx, oc in zip(range(len(cy.scoctet)),cy.scoctet):
                oc.id = idx
                pass
            #print cy.qkoctet
            for idx, oc in zip(range(len(cy.qkoctet)),cy.qkoctet):
                #print idx,oc
                oc.id = idx
                pass
            for idx0, gb3 in zip(range(len(cy.gb3pt)),cy.gb3pt):
                gb3.id = idx0
                #for idx1, tsk in zip(range(len(gb3.sinkTimeslice)),gb3.sinkTimeslice):
                #    tsk.id = str(idx0)+'.'+str(idx1)
                #    for idx2, cor in zip(range(len(tsk.correlator)),tsk.correlator):
                #        cor.id = str(idx0)+'.'+str(idx1)+'.'+str(idx2)
                #        pass
                #    pass
                #pass
        return
    def generate(self,ostream=sys.stdout):
        """Write MILC prompts to output stream 'ostream'."""
        self._bind_indices()
        self.geometry.generate(ostream)
        for x in self.cycle:
            x.generate(ostream)
            pass
        return
    def dataflow(self):
        self._bind_indices()
        w = list()
        for x in self.cycle:
            w.append(x.dataflow())
            pass
        dinfo = { 'title': self.pName, 'workflow': w }
        return dinfo
    pass

class _Cycle_ks_spectrum:
    def __init__(self):
        self.gauge = None
        self.gb3ptOn = False
        self.bsource = list()
        self.msource = list()
        self.nextpropidx = 0
        self.pset = list()
        self.quark = list()
        self.meson = list()
        self.baryon = list()
        self.scoctet = list()
        self.qkoctet = list()
        self.gbbaryon = list()
        self.gb3pt = list()
        return
    def generate(self,ostream):
        self.gauge.generate(ostream)
        print>>ostream, 'max_number_of_eigenpairs 0'
        print>>ostream, 'number_of_pbp_masses 0'
        print>>ostream, 'number_of_base_sources', len(self.bsource)
        for x in self.bsource:
            x.generate(ostream)
            pass
        print>>ostream, 'number_of_modified_sources', len(self.msource)
        for x in self.msource:
            x.generate(ostream)
            pass
        print>>ostream, 'number_of_sets', len(self.pset)
        for x in self.pset:
            x.generate(ostream)
        print>>ostream, 'number_of_quarks', len(self.quark)
        for x in self.quark:
            x.generate(ostream)
            pass
        print>>ostream, 'number_of_mesons', len(self.meson)
        for x in self.meson:
            x.generate(ostream)
        print>>ostream, 'number_of_baryons', len(self.baryon)
        for x in self.baryon:
            x.generate(ostream)
        if True:
        #if len(self.gb3pt) > 0 or self.gb3ptOn:
            #print>>ostream, 'number_of_source_octets', len(self.scoctet)
            #for x in self.scoctet:
            #    x.generate(ostream)
            pass
        print>>ostream, 'number_of_quark_octets', len(self.qkoctet)
        for x in self.qkoctet:
            x.generate(ostream)
        print>>ostream, 'number_of_gb_baryons', len(self.gbbaryon)
        for x in self.gbbaryon:
            x.generate(ostream)
        if len(self.gb3pt) > 0 or self.gb3ptOn:
            #print>>ostream, 'number_of_gb_3pt_sources', len(self.gb3pt)
            #for x in self.gb3pt:
            #    x.generate(ostream)
            pass
        return
    def dataflow(self):
        dinfo = list()
        dinfo.append(self.gauge.dataflow())
        for x in self.bsource:
            dinfo.append(x.dataflow())
            pass
        for x in self.msource:
            dinfo.append(x.dataflow())
            pass
        for x in self.pset:
            for y in x.dataflow():
                dinfo.append(y)
                pass
            pass
        for x in self.quark:
            dinfo.append(x.dataflow())
            pass
        for x in self.meson:
            dinfo.append(x.dataflow())
            pass
        for x in self.baryon:
            dinfo.append(x.dataflow())
            pass
        for x in self.qkoctet:
            dinfo.append(x.dataflow())
            pass
        for x in self.gbbaryon:
            dinfo.append(x.dataflow())
            pass
        for x in self.gb3pt:
            dinfo.append(x.dataflow())
            pass
        return dinfo
    pass
