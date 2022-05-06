Module stereo_robot.calibration.config
======================================
configuration handler for stereo_robot calibration
Description:
    Provides identifier support to access, change and save calibration parameters.

TODO:
    None

Classes
-------

`Config(config_file='default_config.json', value=None, master=None)`
:   ! The configuration class.
    Provides identifier support to access, change and save calibration.
    
    ! The configuration class initializer.
    @param config_file the location of the configuration file. Defaults to "default_config.json"

    ### Methods

    `add_new_entry(self, key, value)`
    :   ! Adds a new entry to the Config class. You can use the publish_values to commit them to a config.json file.
        
        @param key (str) - the name of the variable you would like to store.
        
        @param value (any) - the content that will be stored in config.key.

    `publish_values(self, config_file=None)`
    :   ! Saves the values of the current config class to a json file. This can be called from the parent or any of its children dictionaries.
        
        @param config_file the location of the destination configuration file. If left as None, it  will default to the config_file defined in __init__. If the config_file in __init__ is "default_config.json", then it will not overwrite it and instead save into config.json