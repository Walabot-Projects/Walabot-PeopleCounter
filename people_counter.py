from __future__ import print_function # WalabotAPI works on both Python 2 an 3.
from sys import platform
from os import system
from imp import load_source
from enum import Enum

import WalabotAPI as walabotAPI
walabotAPI.Init()

def PrintTrackerTargets(targets):
    system('cls' if platform == 'win32' else 'clear')
    if targets:
        for i, target in enumerate(targets):
            print(('y: {}'.format(target.yPosCm)))
    else:
        print('No Target Detected')


##################################################
#######   People Counter Class and Logic   #######
##################################################

#           ----------------------------
#  Outside |             |              |  Inside
#    The   |    Back     |    Front     |   the
#    Room  |             |              |   Room
#           ----------------------------

class Placement(Enum):
    Empty = 0  # Target not in the arena
    Back = 1  # Target in the back of the arena
    Front = 2  # Target in the front of the arena


class State(Enum):
    Idle = 0  # Nobody in the arena
    Bi = 1  # In the back - coming in
    Fi = 2  # In the front - coming in
    Bo = 3  # In the back - coming out
    Fo = 4  # In the front - coming out


def _get_placement(targets):
    if len(targets) is 0:
        return Placement.Empty
    if targets[0].yPosCm > 0:
        return Placement.Front
    if targets[0].yPosCm <= 0:
        return Placement.Back


class PeopleCounter:
    def __init__(self):
        self.placement = Placement.Empty
        self.state = State.Idle
        self.count = 0
        self.state_machine = {
            State.Idle:
                {Placement.Empty: State.Idle,
                 Placement.Back: State.Bi,
                 Placement.Front: State.Fo},
            State.Bi:
                {Placement.Empty: State.Idle,
                 Placement.Back: State.Bi,
                 Placement.Front: State.Fi},
            State.Fi:
                {Placement.Empty: State.Idle,  # increment
                 Placement.Back: State.Bi,
                 Placement.Front: State.Fi},
            State.Fo:
                {Placement.Empty: State.Idle,
                 Placement.Back: State.Bo,
                 Placement.Front: State.Fo},
            State.Bo:
                {Placement.Empty: State.Idle,  # increment
                 Placement.Back: State.Bo,
                 Placement.Front: State.Fo},
        }

    def update_state_get_count(self, targets):
        self.placement = _get_placement(targets)
        prev_state = self.state
        self.state = self.state_machine[self.state][self.placement]

        if prev_state == State.Bo and self.state == State.Idle:
            self._decrement()
        elif prev_state == State.Fi and self.state == State.Idle:
            self._increment()

        return self.count

    def _increment(self):
        self.count += 1
        return State.Idle

    def _decrement(self):
        self.count = max(self.count - 1, 0)
        return State.Idle


def PeopleCounterApp():
    # PeopleCounter object
    people_counter = PeopleCounter()
    # walabotAPI.SetArenaR - input parameters
    rArenaMin, rArenaMax, rArenaRes = 5, 120, 5
    # walabotAPI.SetArenaPhi - input parameters
    phiArenaMin, phiArenaMax, phiArenaRes = -60, 60, 3
    # walabotAPI.SetArenaTheta - input parameters
    thetaArenaMin, thetaArenaMax, thetaArenaRes = -20, 20, 10
    # Configure Walabot database install location (for windows)
    walabotAPI.SetSettingsFolder()
    # 1) Connect: Establish communication with walabot.
    walabotAPI.ConnectAny()
    # 2) Configure: Set scan profile and arena
    # Set Profile - to Tracker.
    walabotAPI.SetProfile(walabotAPI.PROF_TRACKER)
    # Set arena by Polar coordinates, with arena resolution
    walabotAPI.SetArenaR(rArenaMin, rArenaMax, rArenaRes)
    walabotAPI.SetArenaPhi(phiArenaMin, phiArenaMax, phiArenaRes)
    walabotAPI.SetArenaTheta(thetaArenaMin, thetaArenaMax, thetaArenaRes)
    # Walabot filtering MTI
    walabotAPI.SetDynamicImageFilter(walabotAPI.FILTER_TYPE_MTI)
    # 3) Start: Start the system in preparation for scanning.
    walabotAPI.Start()

    try:
        num_of_people = 0
        while True:
            # 4) Trigger: Scan (sense) according to profile and record signals
            # to be available for processing and retrieval.
            walabotAPI.Trigger()
            # 5) Get action: retrieve the last completed triggered recording
            targets = walabotAPI.GetTrackerTargets()
            # 6) Sort targets by amplitude
            targets = sorted(targets, key=lambda x: x.zPosCm, reverse=True)
            # 7) Update state and get people count
            prev_num_of_people = num_of_people
            num_of_people = people_counter.update_state_get_count(targets)
            if prev_num_of_people != num_of_people:
                print('# {} #\n'.format(num_of_people))
                # print y-axis of target found
                # PrintTrackerTargets(targets)
    except KeyboardInterrupt:
        pass
    finally:
        # 7) Stop and Disconnect.
        walabotAPI.Stop()
        walabotAPI.Disconnect()
        walabotAPI.Clean()
    print('Terminated successfully!')


if __name__ == '__main__':
    PeopleCounterApp()
