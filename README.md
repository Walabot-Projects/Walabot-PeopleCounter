# WalaHost - A Walabot Application

This is a simple Walabot application that detects people entering / exiting rooms.


The code is written in Python and works on both Python 2 and Python 3.  
The app was tested on Windows 10, Ubuntu 16.04 LTS and Raspberry Pi 3.

##### What does the Walabot Do?

The app uses the Walabot sensor to detect people inside it's arena (around the door header).  
The Y axis is used to determine the location of a person relative to the door.  
A positive number means there's a person outside the door, a negative number means there's someone inside.  
The X and Z axes are ignored (roughly) in this app.

### How to Use

1. [Install the Walabot SDK.](http://api.walabot.com/_install.html)
2. Raspberry Pi only: Configure it to work with Walabot (explained below).
3. Attach the Walabot to the center of your door header (explained below).
4. Run `WalaHost.py` and follow the instructions.

**IMPORTANT NOTE:** Current Walabot settings are for vMaker3 and Raspberry Pi 3.

##### Configure the Raspberry Pi

The Raspberry Pi is an excellent tool for makers, but it is limited in the current it can send to the Walabot.  
Add the following lines to the end of the file at `/boot/config.txt` in order to configure it to work:
```
safe_mode_gpio=4
max_usb_current=1
```
##### Attaching the Walabot to the Door Header

In order of the application to work correctly the Y axis of the Walabot have to be perpendicular to the door header, with the positive side facing outside the room.  
[Take a look here](http://api.walabot.com/_features.html) to verify the coordinate system in your Walabot.

### Editing the Code

At the top of the code you can find variables that can be changed easily without dealing with the "heavy" part of the code.  
All those variables should vary between different Walabot boards, operating systems, operating machines, etc.  
'Walabot Settings' variables are necessary to set the Walabot arena.  
'App Settings' variables are required for a proper flow of the app.

##### Walabot Settings

* `R_MIN, R_MAX, R_RES`: Walabot [`SetArenaR`](http://api.walabot.com/_walabot_a_p_i_8h.html#aac6cafa27c4a7d069dd64c903964632c) parameters. Determines how low (from it's location) the Walabot will "see".
* `THETA_MIN, THETA_MAX, THETA_RES`:  Walabot [`SetArenaTheta`](http://api.walabot.com/_walabot_a_p_i_8h.html#a3832f1466248274faadd6c23127b998d) parameters. The theta axis is ignored in this app, those values should always be the "lowest" possible.
* `PHI_MIN, PHI_MAX, PHI_RES`: Walabot [`SetArenaPhi`]((http://api.walabot.com/_walabot_a_p_i_8h.html#a9afb632b5cce965eba63b323bc579557)) parameters. Used to set how "far" the Walabot will "see" (from it's location).
* `THRESHOLD`: Walabot [`SetThreshold`](http://api.walabot.com/_walabot_a_p_i_8h.html#a4a19aa1afc64d7012392c5c91e43da15) parameter. Lower this value if you wish to detect objects smaller the a man's head.

A comprehensive explanation about the Walabot imaging features can be found [here](http://api.walabot.com/_features.html).

##### App Settings

* `SENSITIVITY`: The amount of time (in seconds) to wait after a move has been detected.
* `TENDENCY_LOWER_BOUND`: Tendency below that won't count as entrance/exit. Helps when people are pausing near the door.
* `IGNORED_LENGTH`: The length (in cm) of a strip in the middle of the arena where targets are ignored. This length goes from the middle to each side (of the door).
