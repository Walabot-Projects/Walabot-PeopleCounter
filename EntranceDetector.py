from __future__ import print_function # WalabotAPI works on both Python 2 an 3.
from sys import platform
from os.path import join
from collections import deque
from imp import load_source

def init_walabot():
    if platform == 'win32': # for windows
        path = join('C:/', 'Program Files', 'Walabot', 'WalabotSDK', 'python')
    else: # for linux, raspberry pi, etc.
        path = join('/usr', 'share', 'walabot', 'python')
    wlbt = load_source('WalabotAPI', join(path, 'WalabotAPI.py'))
    wlbt.Init()
    wlbt.SetSettingsFolder()
    return wlbt
wlbt = init_walabot()

def make_sure_walabot_is_connected():
    while True:
        try:
            wlbt.ConnectAny()
        except wlbt.WalabotError as err:
            if err.code == 19: # 'WALABOT_INSTRUMENT_NOT_FOUND'
                input("- Connect Walabot and press 'Enter'.")
        else:
            print('- Connection to Walabot established.')
            return

def set_walabot_settings():
    wlbt.SetProfile(wlbt.PROF_SENSOR)
    wlbt.SetArenaR(10, 100, 10)
    wlbt.SetArenaTheta(-1, 1, 10)
    wlbt.SetArenaPhi(-1, 1, 10)
    wlbt.SetThreshold(100)
    wlbt.SetDynamicImageFilter(wlbt.FILTER_TYPE_NONE)
    print('- Walabot Configurated.')

def start_and_calibrate_walabot():
    wlbt.Start()
    wlbt.StartCalibration()
    print('- Calibrating...')
    while wlbt.GetStatus()[0] == wlbt.STATUS_CALIBRATING:
        wlbt.Trigger()
    print('- Calibration ended.')

def wait_for_target():
    while True:
        wlbt.Trigger()
        if get_targets(wlbt.GetSensorTargets()):
            return

def wait_for_target_to_pass():
    num_of_no_targets = 0
    while num_of_no_targets < 3:
        wlbt.Trigger()
        if not get_targets(wlbt.GetSensorTargets()):
            num_of_no_targets += 1

def stop_and_disconnect_walabot():
    wlbt.Stop()
    wlbt.Disconnect()
    print('- Walabot disconnected.')

def get_targets(targets):
    if targets:
        for i, target in enumerate(targets):
            if abs(target.yPosCm < 3):
                return True
    return False

def EntranceDetector():
    make_sure_walabot_is_connected()
    set_walabot_settings()
    start_and_calibrate_walabot()
    while True:
        wait_for_target()
        print('Target Found!')
        wait_for_target_to_pass()
    stop_and_disconnect_walabot()

if __name__ == '__main__':
    EntranceDetector()
