#!/usr/bin/env python3
import tkinter.messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons,TextBox
import sys,os
import ctypes  # An included library with Python install.
sys.path.insert(0,
    os.path.join(os.path.dirname(os.path.realpath(__file__)),"..")
    )

from configuration import Config
pi = None
config = Config()

import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showinfo
root = tk.Tk()
root.withdraw()

enablePWM = False
helpmsg = [
"""Mode 1: Add Points
A tool to map a sabertooth's pwm
to voltage conversion.
-----------------------------------
Instructions:
Enable motor and adjust the
freq. sent to a sabertooth motor
driver. Measure the voltage from
the sabertooth using a voltmeter,
and adjust the voltage slider, then
add new points.
-----------------------------------
Keyboard controls:
LFT/RGT - adj PWM freq
UP/DWN - select voltg
Enter  - Add to list
-----------------------------------
Buttons:
ENBL MTR-send signal to pins
Load - load points from a .json file
Save - Save points to a .json file
Mode - Select other tools
? - See info about this tool
""",
"""
Mode 2: Edit Points
A tool to map a sabertooth's pwm
to voltage conversion.
-----------------------------------
Instructions:
Select points to delete them
-----------------------------------
Keyboard controls:
LFT/RGT - select point to edit
UP/DWN - Not implemented
Bckspc  - Delete point

-----------------------------------
Buttons:
ENBL MTR-Not used
Load - load config from a .json file
Save - Save config to a .json file
Mode - Select other tools
? - See info about this tool
""",
"""
Mode 3: Fit Curve
A tool to map a sabertooth's pwm
to voltage conversion.
-----------------------------------
Instructions:
Adjust fit of curve to approximate
the sampled datapoints
-----------------------------------
Keyboard controls:
LFT/RGT - Change curve degree
UP/DWN - Not implemented
Bckspc  - Delete point

-----------------------------------
Buttons:
ENBL MTR-Not used
Load - load config from a .json file
Save - Save config to a .json file
Mode - Select other tools
? - See info about this tool
"""]

fig, ax = plt.subplots()
fig.canvas.set_window_title("Calibrate Sabertooth Motor Driver")
plt.subplots_adjust(left=0.25, bottom=0.3)
volts = np.array([])
freqs = np.array([])
v0 = 10
f0 = 500
deltaF = 1
deltaV = 0.1
#s = a0 * np.sin(2 * np.pi * f0 * t)
#l, = plt.plot(0)#, s, lw=2)

all_points, = plt.plot(freqs,volts,linewidth=0,marker='.',zorder=40)
new_point, = plt.plot(f0,v0,linewidth=0,marker='o',zorder=30)
selected_point, = plt.plot(f0,v0,linewidth=0,marker='o',color='orange',alpha=0,zorder=20)
fit_curve, = plt.plot([],[],color='green',alpha=0,zorder=10)

ax.margins(x=0)
ax.set_title(f"Add Points")
ax.set_xlabel("PWM Frequency")
ax.set_ylabel("Sabertooth Output Voltage")

axcolor = 'lightgoldenrodyellow'
axVolt = plt.axes([0.25, 0.15, 0.65, 0.03], facecolor=axcolor)
axFreq = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor=axcolor)

sFreq = Slider(axFreq, 'Freq', 0, 1250, valinit=f0,valstep=deltaF)
sVolt = Slider(axVolt, 'Volt',0.1, 12.0, valinit=v0, valstep=deltaV)

ax.set_ylim(-12,12)
ax.set_xlim(0,1250)

#buttons
resetax = plt.axes([0.8, 0.025, 0.09, 0.04])
button = Button(resetax, 'Reset', color=axcolor, hovercolor='0.975')

addax = plt.axes([0.7, 0.025, 0.09, 0.04])
addbutton = Button(addax, 'Add', color=axcolor, hovercolor='0.975')

helpax = plt.axes([0.9, 0.025, 0.02, 0.04])
helpbutton = Button(helpax, '?', color=axcolor, hovercolor='0.975')

modes = {'Add':0, 'Edit':1, 'Fit':2}
mode = 0
rax = plt.axes([0.025, 0.35, 0.1, 0.15], facecolor=axcolor)
radio = RadioButtons(rax, tuple(modes.keys()), active=mode)
rax.set_title("Mode",fontsize=8)

enablePWMax = plt.axes([0.025, 0.65, 0.1, 0.15], facecolor=axcolor)
enablePWMax.set_title("ENBL MOTOR",fontsize=8)
enablePWM_buttons = RadioButtons(enablePWMax, ("ON","OFF"), active=1)

textbox_text = "default_config.json"
axbox = plt.axes([0.06, 0.025, 0.25, 0.04])
text_box = TextBox(axbox, 'File: ', initial=textbox_text)

loadax = plt.axes([0.315, 0.025, 0.08, 0.04])
load_button = Button(loadax, 'Load', color=axcolor, hovercolor='0.975')

saveax = plt.axes([0.4, 0.025, 0.08, 0.04])
save_button = Button(saveax, 'Save', color=axcolor, hovercolor='0.975')


## BUTTONS

def update_new_point(val):
    volt = sVolt.val
    freq = sFreq.val
    new_point.set_ydata(volt)
    new_point.set_xdata(freq)
    fig.canvas.draw_idle()

sFreq.on_changed(update_new_point)
sVolt.on_changed(update_new_point)

def resetbutton_pressed(event):
    sFreq.reset()
    sVolt.reset()
button.on_clicked(resetbutton_pressed)

def addbutton_pressed(event):
    global volts,freqs
    volt = sVolt.val
    freq = sFreq.val
    
    volts = np.append(volts,volt)
    freqs = np.append(freqs,freq)
    all_points.set_ydata(volts)
    all_points.set_xdata(freqs)
    fig.canvas.draw_idle()
addbutton.on_clicked(addbutton_pressed)

def helpbutton_pressed(event):
    def popup_showinfo():
        showinfo("Window", helpmsg[mode],icon="question")
    popup_showinfo()
helpbutton.on_clicked(helpbutton_pressed)

def load_points(val):
    global freqs,volts,config
    config = Config(textbox_text)
    freqs = config.MOTOR.FREQS
    volts = config.MOTOR.VOLTS
    all_points.set_ydata(volts)
    all_points.set_xdata(freqs)
    fig.canvas.draw_idle()
load_button.on_clicked(load_points)

def save_points(val):
    msg = "NOT IMPLEMENTED"
    print(msg)
    showinfo("Window", msg,icon="question")

    return
    global freqs,volts,config
    config = Config(textbox_text)
    freqs = config.MOTOR.FREQS
    volts = config.MOTOR.VOLTS
    all_points.set_ydata(volts)
    all_points.set_xdata(freqs)
    fig.canvas.draw_idle()
save_button.on_clicked(save_points)


def update_text(val):
    global textbox_text
    textbox_text=val
text_box.on_text_change(update_text)


## SWITCHES

def togglePWM(label):
    global enablePWM,pi
    if label == "ON":
        enablePWM = True
        if pi is None:
            import pigpio
            pi = pigpio.pi()
            pi.set_mode(config.MOTOR.PIN_MTR_L,pigpio.OUTPUT)
            pi.set_mode(config.MOTOR.PIN_MTR_R,pigpio.OUTPUT)
            pi.hardware_PWM(config.MOTOR.PIN_MTR_L,0,config.MOTOR.MTR_PWMduty)
            pi.hardware_PWM(config.MOTOR.PIN_MTR_R,0,config.MOTOR.MTR_PWMduty)
    else:
        enablePWM = False
enablePWM_buttons.on_clicked(togglePWM)


def modefunc(label):
    global mode,ax,fit_curve_degree
    mode = modes[label]
    if mode == 0:
        new_point.set_alpha(1)
        selected_point.set_alpha(0)
        fit_curve.set_alpha(0)
        ax.set_title(f"Add Points")
    if mode == 1:
        new_point.set_alpha(0)
        selected_point.set_alpha(1)
        fit_curve.set_alpha(0)
        if len(volts)!=0:
            currently_selected_ind = 0
            selected_point.set_ydata(volts[0])
            selected_point.set_xdata(freqs[0])
        ax.set_title(f"Edit Points")
    if mode == 2:
        new_point.set_alpha(0)
        selected_point.set_alpha(0)
        fit_curve.set_alpha(1)
        fit_curve_degree = max(min(fit_curve_degree,len(volts)-1),1)
        ax.set_title(f"Fit Curve, n = {fit_curve_degree}")
        
    fig.canvas.draw_idle()
radio.on_clicked(modefunc)

## KEYBOARD EVENTS

import time
tlast=time.time()
accel_scroll_counter = 1
def accel_scroll():
    global tlast,accel_scroll_counter
    t = time.time()
    if t-tlast<0.1:
        accel_scroll_counter+=1
    else:
        accel_scroll_counter=0
    x =accel_scroll_counter*0.5
    tlast=t
    return int((50/(1+np.exp(-0.8*(x-5)))+1))

currently_selected_ind = 0
fit_curve_degree = 1

#all keyboard events
def on_press(event):
    global currently_selected_ind,mode,fit_curve_degree, volts, freqs
#    print('press',event.key)
    sys.stdout.flush()
    if (mode == 0):
        if event.key == 'right':
            sFreq.set_val(sFreq.val+deltaF*accel_scroll())
        if event.key == 'left':
            sFreq.set_val(sFreq.val-deltaF*accel_scroll())
        if event.key == 'up':
            sVolt.set_val(sVolt.val+deltaV*accel_scroll())
        if event.key == 'down':
            sVolt.set_val(sVolt.val-deltaV*accel_scroll())
        if event.key == 'enter':
            addbutton_pressed(None)
        if enablePWM:
            print(f"Setting Sabertooth to {sFreq.val}")
            try:
                pi.hardware_PWM(config.MOTOR.PIN_MTR_L,sFreq.val,config.MOTOR.MTR_PWMduty)
                pi.hardware_PWM(config.MOTOR.PIN_MTR_R,sFreq.val,config.MOTOR.MTR_PWMduty)
            except Exception as E:
                print(E)
                def popup_showinfo():
                    msg = "Error while setting PWM with pigpio. See Error msg"
                    msg+= "in terminal.\n"
                    msg+= "Try starting pigpio daemon (sudo pigpiod)"
                    showinfo("Window", msg,icon="question")
                popup_showinfo()
                
    
    if (mode == 1) and (len(volts) != 0):
        if event.key == 'right':
            currently_selected_ind = min(currently_selected_ind+1,len(volts)-1)
        if event.key == 'left':
            currently_selected_ind = max(currently_selected_ind-1,0)
        if event.key == 'backspace':
            volts = np.delete(volts,currently_selected_ind)
            freqs = np.delete(freqs,currently_selected_ind)
            if len(volts)==0:
                return
            currently_selected_ind = max(0,currently_selected_ind-1)
        volt = volts[currently_selected_ind]
        freq = freqs[currently_selected_ind]
        all_points.set_ydata(volts)
        all_points.set_xdata(freqs)
        selected_point.set_ydata(volt)
        selected_point.set_xdata(freq)
    
    if (mode == 2):
        if (len(volts) >=2):
            if event.key == 'left':
                fit_curve_degree = max(min(fit_curve_degree-1,len(volts)-1),1)
            if event.key == 'right':
                fit_curve_degree = max(min(fit_curve_degree+1,len(volts)-1),1)
            fit_volts = np.linspace(-12,12)
            fit_fun_coeff = np.polyfit(volts,freqs,fit_curve_degree)
            fit_fun = np.poly1d(fit_fun_coeff)
            fit_freqs = fit_fun(fit_volts)
            fit_curve.set_ydata(fit_volts)
            fit_curve.set_xdata(fit_freqs)
        else:
            fit_curve_degree = 0

        ax.set_title(f"Fit Curve, n = {fit_curve_degree}")
    fig.canvas.draw_idle()

fig.canvas.mpl_connect('key_press_event', on_press)



plt.show()
root.destroy()
