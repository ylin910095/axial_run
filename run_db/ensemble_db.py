import sys,os

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.sql import text
from sqlalchemy.engine import reflection

Declare = declarative_base()

class Ensemble(Declare):
    __tablename__ = "ensemble"
    id = Column(Integer, Sequence('ensemble_seq'), primary_key=True)
    name = Column(String)
    max_jobs = Column(Integer) # TODO: make sepearte tables for cluster params
    check_jobs_command = Column(String)
    cluster_param = Column(String) # slurm setup info

    # Establish children
    configuration = relationship("Configuration", back_populates="ensemble")
    def __init__(self, ensemble_name, max_jobs, check_jobs_command, cluster_param):
        self.name = ensemble_name
        self.max_jobs = max_jobs
        self.check_jobs_command = check_jobs_command
        self.cluster_param = cluster_param

class PromptParam(Declare):
    __tablename__ = "pmt_param"
    id = Column(Integer, Sequence('pmt_param_seq'), primary_key=True)
    pmt_file = Column(String)
    param_dict = Column(String) # input to the pmt file
    name_tag = Column(String) # name tag for this pmt_param run
                              # for safety, we don't assume it is unique
    # Children
    configuration = relationship("Configuration", back_populates="pmt_param")

    def __init__(self, pmt_file, param_dict, name_tag):
        self.pmt_file = os.path.abspath(os.path.realpath(pmt_file)) # always put the real paths
        self.param_dict = param_dict # sting dump by yaml.dump 
        self.name_tag = name_tag # we dont assume they are unique

class Configuration(Declare):
    __tablename__ = "configuration"
    id = Column(Integer, Sequence('configuration_seq'), primary_key=True)
    ensemble_id = Column(Integer, ForeignKey('ensemble.id'), nullable=False)
    pmt_param_id = Column(Integer, ForeignKey('pmt_param.id'), nullable=False)

    configuration = Column(String)
    md5_checksums = Column(String)
    series = Column(String)
    trajectory = Column(Integer)
    time_stamp = Column(String, nullable=True)
    running_hash = Column(String, nullable=True)
    run1_status = Column(String, nullable=True) # Incomplete, Running, Complete
    run1_binary_md5 = Column(String, nullable=True) # Hash the MILC executable
    run1_hostname = Column(String, nullable=True)
    run1_jobid = Column(String,  nullable=True)
    run1_script = Column(String,  nullable=True)

    # Parent
    ensemble = relationship("Ensemble", back_populates="configuration")
    pmt_param = relationship("PromptParam", back_populates="configuration")

    def __init__(self, ensemble_id, pmt_param_id, configuration, 
                 md5_checksums, series, trajectory):
        """
        Initilize all gauge configurations. The gauge file location stored 
        in the database will always be its abosolute path, stripping of any 
        links
        """
        init_dict = {"ensemble_id":ensemble_id, "pmt_param_id":pmt_param_id, 
                     "configuration":os.path.abspath(os.path.realpath(configuration)),
                     "md5_checksums":md5_checksums, 
                     "series": series, "trajectory":trajectory}
        self.update(init_dict)

    def update(self, update_dict, check_exist=True):
        attribute_list = ["ensemble_id", "pmt_param_id", 
                          "configuration", "md5_checksums", "series", 
                          "trajectory", "time_stamp", 
                          "running_hash", "run1_status",
                          "run1_binary_md5", "run1_hostname", "run1_jobid", "run1_script"]
        for key in update_dict:
            if key in attribute_list:
                if check_exist:
                    getattr(self, key) # raise error if such attribute does not exist
                setattr(self, key, update_dict[key])
