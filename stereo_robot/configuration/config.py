#"""! @brief configuration handler for stereo_robot calibration """
##
# @file config.py
#
# @brief configuration handler for stereo_robot calibration
#
# @section description_config Description
# Provides identifier support to access, change and save calibration
# parameters.
#
# @section notes_config Notes
# - Comments are Doxygen compatible.
#
# @section todo_config TODO
# - None.
#
# @section author_config Author(s)
# - Created by John Woolsey on 05/27/2020.
# - Modified by John Woolsey on 06/11/2020.
#
# Copyright (c) 2020 Woolsey Workshop.  All rights reserved.


"""
configuration handler for stereo_robot calibration
Description:
    Provides identifier support to access, change and save calibration parameters.

TODO:
    None
"""

import json,os

os.chdir(os.path.dirname(os.path.realpath(__file__)))

class Config:
    """! The configuration class.
    Provides identifier support to access, change and save calibration.
    """
    def __init__(self,config_file="default_config.json",_root=[],_key="",value=None,master=None):
        """! The configuration class initializer.
        @param config_file the location of the configuration file. Defaults to "default_config.json"
        """
        self._root = _root.copy()
        self._root.append(_key)
        self.config_file=config_file
        if master is None:
            self.master = self
        else:
            self.master = master
        
        if _key == "" and value is None:
            assert '.json' in config_file.lower()
            with open(config_file,'r') as f:
                config_dict = json.load(f)
        else:
            config_dict = value
            
        for k,v in config_dict.items():
            if type(v) == dict:
                setattr(self,k,Config(config_file,self._root,k,v))
            else:
                setattr(self,k,v)
        
        self.config_dict = config_dict
        
    def publish_values(self,config_file=None):
        """! Saves the values of the current config class to a json file. This can be called from the parent or any of its children dictionaries.
        
        @param config_file the location of the destination configuration file. If left as None, it  will default to the config_file defined in __init__. If the config_file in __init__ is "default_config.json", then it will not overwrite it and instead save into config.json
        """
        if config_file is None:
            if self.config_file == "default_config.json":
                config_file = "config.json"
            else:
                config_file = self.config_file
        
        master_json = self.master._get_values()
        
        with open(config_file,'w') as f:
            json.dump(master_json,f)
            
    def _get_values(self):
        return_dict = {}
        for k,v in self.config_dict.items():
            if type(v) is dict:
                return_dict[k] = getattr(self,k)._get_values()
            else:
                return_dict[k]=getattr(self,k)
        return return_dict
    
    def add_new_entry(self,key,value):
        """! Adds a new entry to the Config class. You can use the publish_values to commit them to a config.json file.
        
        @param key (str) - the name of the variable you would like to store.
        
        @param value (any) - the content that will be stored in config.key.
        """
        self.config_dict[key] = value
        setattr(self,key,value)
        
if __name__=="__main__":

    config = Config()
    
    print(config._get_values())
    print(config.THRESH.HI)
