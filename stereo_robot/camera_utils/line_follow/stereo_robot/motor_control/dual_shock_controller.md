Module stereo_robot.motor_control.dual_shock_controller
=======================================================

Functions
---------

    
`client(q)`
:   

Classes
-------

`MyController(pipe, **kwargs)`
:   Actions are inherited in the Controller class.
    In order to bind to the controller events, subclass the Controller class and
    override desired action events in this class.
    
    Initiate controller instance that is capable of listening to all events on specified input interface
    :param interface: STRING aka /dev/input/js0 or any other PS4 Duelshock controller interface.
                      You can see all available interfaces with a command "ls -la /dev/input/"
    :param connecting_using_ds4drv: BOOLEAN. If you are connecting your controller using ds4drv, then leave it set
                                             to True. Otherwise if you are connecting directly via directly via
                                             bluetooth/bluetoothctl, set it to False otherwise the controller
                                             button mapping will be off.

    ### Ancestors (in MRO)

    * pyPS4Controller.controller.Controller
    * pyPS4Controller.controller.Actions

    ### Methods

    `on_L3_down(self, value)`
    :

    `on_L3_left(self, value)`
    :

    `on_L3_right(self, value)`
    :

    `on_L3_up(self, value)`
    :

    `on_L3_x_at_rest(self)`
    :   L3 joystick is at rest after the joystick was moved and let go off

    `on_L3_y_at_rest(self)`
    :   L3 joystick is at rest after the joystick was moved and let go off

    `on_circle_press(self)`
    :

    `on_circle_release(self)`
    :

    `on_disconnect(self)`
    :

    `on_triangle_press(self)`
    :

    `on_triangle_release(self)`
    :

    `on_x_press(self)`
    :

    `on_x_release(self)`
    :

    `write_controller(self)`
    :