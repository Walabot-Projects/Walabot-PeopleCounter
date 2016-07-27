from __future__ import print_function # python2-python3 compatibillity
try: input = raw_input # python2-python3 compatibillity
except NameError: pass # python2-python3 compatibillity
from sys import platform
from os.path import join
from imp import load_source # used to load the walabot library
from datetime import datetime, timedelta # used to the current time
from string import digits # the string '0123456789'
from math import sin, cos, radians, sqrt # used to calculate MAX_Y_VALUE
from os import system

R_MIN, R_MAX, R_RES = 10, 60, 2 # walabot SetArenaR parameters
THETA_MIN, THETA_MAX, THETA_RES = -10, 10, 10 # walabot SetArenaTheta parameters
PHI_MIN, PHI_MAX, PHI_RES = -10, 10, 2 # walabot SetArenaPhi parametes
THRESHOLD = 15 # walabot SetThreshold parametes
MAX_Y_VALUE = R_MAX * cos(radians(THETA_MAX)) * sin(radians(PHI_MAX))
SENSITIVITY = 0.25 # amount of seconds to wait after a move has been detected
TENDENCY_LOWER_BOUND = 0.1 # tendency below that won't count as entrance/exit
IGNORED_LENGTH = 5 # len in cm to ignore targets in center of arena (each side)

def initWalabot():
    """ Load and initialize the Walabot SDK. A cross platform function.
        Returns:
            wlbt:           The WalabotAPI module
    """
    if platform == 'win32': # for windows
        path = join('C:/', 'Program Files', 'Walabot', 'WalabotSDK', 'python')
    else: # for linux, raspberry pi, etc.
        path = join('/usr', 'share', 'walabot', 'python')
    wlbt = load_source('WalabotAPI', join(path, 'WalabotAPI.py'))
    wlbt.Init()
    wlbt.SetSettingsFolder()
    return wlbt
wlbt = initWalabot()

def getNumOfPeopleInside():
    """ Gets the current number of people in the room as input and returns it.
        Validate that the number is valid.
        Returns:
            num             Number of people in the room that got as input
    """
    num = input('- Enter current number of people in the room: ')
    if not num:
        print('- Invalid input, try again.')
        return getNumOfPeopleInside()
    for digit in num:
        if digit not in digits:
            print('- Invalid input, try again.')
            return getNumOfPeopleInside()
    if int(num) < 0:
        print('- Invalid input, try again.')
        return getNumOfPeopleInside()
    return int(num)

def verifyWalabotIsConnected():
    """ Check for Walabot connectivity. loop until detect a Walabot.
    """
    while True:
        try:
            wlbt.ConnectAny()
        except wlbt.WalabotError as err:
            if err.code == 19: # 'WALABOT_INSTRUMENT_NOT_FOUND'
                input("- Connect Walabot and press 'Enter'.")
        else:
            print('- Connection to Walabot established.')
            return

def setWalabotSettings():
    """ Configure Walabot's profile, arena (r, theta, phi), threshold and
        the image filter.
    """
    wlbt.SetProfile(wlbt.PROF_SENSOR)
    wlbt.SetArenaR(R_MIN, R_MAX, R_RES)
    wlbt.SetArenaTheta(THETA_MIN, THETA_MAX, THETA_RES)
    wlbt.SetArenaPhi(PHI_MIN, PHI_MAX, PHI_RES)
    wlbt.SetThreshold(THRESHOLD)
    wlbt.SetDynamicImageFilter(wlbt.FILTER_TYPE_NONE)
    print('- Walabot Configurated.')

def startAndCalibrateWalabot():
    """ Start the Walabot and calibrate it.
    """
    wlbt.Start()
    wlbt.StartCalibration()
    print('- Calibrating...')
    while wlbt.GetStatus()[0] == wlbt.STATUS_CALIBRATING:
        wlbt.Trigger()
    print('- Calibration ended.\n- Ready!')

def getDataList():
    """ Detect and record a list of Walabot sensor targets. Stop recording
        and return the data when enough triggers has occured (according to the
        SENSITIVITY) with no detection of targets.
        Returns:
            dataList:      A list of the yPosCm attribute of the detected
                            sensor targets
    """
    while True:
        wlbt.Trigger()
        targets = wlbt.GetSensorTargets()
        distance = lambda t: sqrt(t.xPosCm**2 + t.yPosCm**2 + t.zPosCm**2)
        if targets:
            targets = [max(targets, key=distance)]
            numOfFalseTriggers = 0
            triggersToStop = wlbt.GetAdvancedParameter('FrameRate')*SENSITIVITY
            while numOfFalseTriggers < triggersToStop:
                wlbt.Trigger()
                newTargets = wlbt.GetSensorTargets()
                if newTargets:
                    targets.append(max(newTargets, key=distance))
                    numOfFalseTriggers = 0
                else:
                    numOfFalseTriggers += 1
            yList = [t.yPosCm for t in targets if abs(t.yPosCm)>IGNORED_LENGTH]
            if yList:
                return yList

def analizeAndAlert(dataList, numOfPeople):
    """ Analize a given dataList and print to the screen one of two results
        if occured: an entrance or an exit.
        Arguments:
            dataList        A list of values
            numOfPeople     The current number of people in the room
        returns:
            numOfPeople     The new number of people in the room
    """
    currentTime = datetime.now().strftime('%H:%M:%S')
    tendency = getTypeOfMovement(dataList)
    if tendency > 0:
        result = ': Someone has left!'.ljust(25)
        numOfPeople -= 1
    elif tendency < 0:
        result = ': Someone has entered!'.ljust(25)
        numOfPeople += 1
    else: # do not count as a valid entrance / exit
        result = ': Someone is at the door!'.ljust(25)
    numToDisplay = ' Currently '+str(numOfPeople)+' people in the room.'
    print(currentTime+result+numToDisplay)
    return numOfPeople

def getTypeOfMovement(dataList):
    """ Calculate and return the type of movement detected.
        The movement only counts as a movement inside/outside if the tendency
        if above TENDENCY_LOWER_BOUND and if the we have at least of item from
        both sides of the door header.
        Arguments:
            dataList        A list of values
        Returns:
            tendency        if zero - not count as a valid entrance/exit
                            if positive - counts as exiting the room
                            if negative - counts as entering the room
    """
    if dataList:
        velocity, length = getVelocityAndLength(dataList)
        tendency = (velocity * length) / (2 * MAX_Y_VALUE)
        bothSides = any(x>0 for x in dataList) and any(x<0 for x in dataList)
        aboveLowerBound = abs(tendency) > TENDENCY_LOWER_BOUND
        if bothSides or aboveLowerBound:
            return tendency
    return 0

def getVelocityAndLength(dataList):
    """ Calculate the slope (velocity) of a given set of values using linear
        regression, and the number of given values.
        Arguments:
            dataList        A list of values
        Returns:
            slope           the slope of an estimated linear regression
            length          the length of dataList
    """
    Sx = Sy = Sxx = Sxy = 0
    for x, y in enumerate(dataList):
        Sx, Sy, Sxx, Sxy = Sx + x, Sy + y, Sxx + x**2, Sxy + x*y
    try:
        return (Sxy * (x+1) - Sy * Sx) / (Sxx * (x+1) - Sx * Sx), x + 1
    except ZeroDivisionError:
        return 0, 0

def stopAndDisconnectWalabot():
    """ Stops Walabot and disconnect the device.
    """
    wlbt.Stop()
    wlbt.Disconnect()

def WalaHost():
    """ Main function. init and configure the Walabot, get the current number
        of people from the user, start the main loop of the app.
        Walabot scan constantly and record sets of data (when peoples are
        near the door header). For each data set, the app calculates the type
        of movement recorded and acts accordingly.
    """
    verifyWalabotIsConnected()
    numOfPeople = getNumOfPeopleInside()
    setWalabotSettings()
    startAndCalibrateWalabot()
    try:
        while True:
            dataList = getDataList()
            numOfPeople = analizeAndAlert(dataList, numOfPeople)
    except KeyboardInterrupt: pass
    finally:
        stopAndDisconnectWalabot()

if __name__ == '__main__':
    WalaHost()