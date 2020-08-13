import sys

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

    # Establish children
    configuration = relationship("Configuration", back_populates="ensemble")
    def __init__(self, ensemble_name):
        self.name = ensemble_name

class Configuration(Declare):
    __tablename__ = "configuration"
    id = Column(Integer, Sequence('configuration_seq'), primary_key=True)
    ensemble_id = Column(Integer, ForeignKey('ensemble.id'), nullable=False)

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

    def __init__(self, ensemble_id, configuration, md5_checksums, series, trajectory):
        """
        Initilize all gauge configurations
        """
        init_dict = {"ensemble_id":ensemble_id, "configuration":configuration,
                     "md5_checksums":md5_checksums, "series": series, "trajectory":trajectory}
        self.update(init_dict)

    def update(self, update_dict, check_exist=True):
        attribute_list = ["ensemble_id", "configuration", "md5_checksums", "series", 
                          "trajectory", "time_stamp", "running_hash", "run1_status",
                          "run1_binary_md5", "run1_hostname", "run1_jobid", "run1_script"]
        for key in update_dict:
            if key in attribute_list:
                if check_exist:
                    getattr(self, key) # raise error if such attribute does not exist
                setattr(self, key, update_dict[key])

