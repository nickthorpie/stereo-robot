Module stereo_robot.motor_control.direction_control
===================================================

Classes
-------

`DirectionControl(config)`
:   

    ### Methods

    `add_dead_reckon_straight(self, dist)`
    :

    `add_dead_reckon_turn(self, degrees)`
    :

    `barcode_routine(self, camera_state)`
    :

    `calc_line_force(self, camera_state)`
    :

    `dead_reckon_step(self)`
    :   TODO: Maybe should pass current_time as an arg if we're using
        it elsewhere?

    `djikstra_turn(self, barcode)`
    :

    `do_lost_sweep(self, camera_state)`
    :

    `is_new_barcode(self, barcode)`
    :

    `lost_routine(self, camera_state)`
    :

    `lost_step(self, camera_state)`
    :

    `step(self, controller_state, camera_state)`
    :