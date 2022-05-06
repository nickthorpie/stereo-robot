Module stereo_robot.main
========================
DS4_cartcontrol.py
DESCRIPTION:
    Controls a sabertooth dual motor with a sony DS4 remote on a RPi4.
    
NOTES:
    Multithreading is used to listen to the controller in a separate process.
    A Queue is used to deliver the most recent command as a JSON string.
    PROGRAM 1: Controller Client
        Reads the controller using pyPS4Controller Library.
        Changes in left joystick position are written to queue as 'vert' and 'horz'.
        Joystick map is +/-32767
        Be sure to connect DS4 in bluetooth first using RPI's 
        
    PROGRAM 2: Motor Server
        Reads out of the queue, and sends PWM signals to the two motor driver signals
        Currently all pinouts are hardcoded as GPIO 12 and 13. Duty cycle 50%.
        The sabertooth switch configuation is in RC mode as follows:
        | 1 | 2 | 3 | 4 | 5 | 6 |
        |DWN| UP| UP| UP| UP|DWN|
        In RC Mode, motor direction is a function of PWM frequency. These may/will
        change depending on configuration (input voltage, driver, duty cycle, gremlins).
        The mapping of frequencies to output voltage were collected by hand in
        SABERTOOTH_VOLTAGE_FREQ_MAP.ipynb, and are fit with a quadratic function.