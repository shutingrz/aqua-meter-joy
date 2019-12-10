#!/usr/bin/python3

from inputs import get_gamepad
import can
import time
import sys
from threading import Thread


canactions = {
    "setShiftD": {"id": 0x3bc, "data":[0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00]},
    "setShiftB": {"id": 0x3bc, "data":[0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00]},
    "setShiftN": {"id": 0x3bc, "data":[0x00, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]},
    "setShiftR": {"id": 0x3bc, "data":[0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]},
    "setShiftP": {"id": 0x3bc, "data":[0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]},
}

regularActions = {
    "suppressWarning1": {"id": 0x3b7, "data":[0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]},
    "suppressWarning2": {"id": 0x394, "data":[0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]},
    "setTemperature":   {"id": 0x3b0, "data":[0x00, 0x00, 0x00, 0x44, 0x00, 0x00, 0x00, 0x00]},
    "setReadyLamp":     {"id": 0x3b6, "data":[0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00]},
    "setEVMeter":       {"id": 0x247, "data":[0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]}
}

throttle = {"id": 0x0b4, "data":[0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00], "valve": 0}

class RegularCANTask(Thread):
    def __init__(self, bus, **kwargs):
        super(RegularCANTask, self).__init__(**kwargs)
        self.bus = bus
    
    def run(self):
        while True:
            for action in regularActions.values():
                msg = can.Message(arbitration_id=action["id"], data=action["data"], extended_id=False)
                self.bus.send(msg)
                time.sleep(0.1)


class ControlThrottleTask(Thread):
    def __init__(self, bus, **kwargs):
        super(ControlThrottleTask, self).__init__(**kwargs)
        self.bus = bus
    
    def run(self):
        while True:
            action = throttle
            action["data"][5] = int(action["valve"] * (28/100))
            interval = 1 - throttle["valve"]/256
            msg = can.Message(arbitration_id=action["id"], data=action["data"], extended_id=False)
            self.bus.send(msg)
            time.sleep(interval)


def main():
    bus = can.interface.Bus('can0', bustype='socketcan')

    temp = 0x44
    RegularCANTask(bus).start()
    ControlThrottleTask(bus).start()

    while True:
        events = get_gamepad()
        for event in events:
            if event.code == "SYN_REPORT":
                pass
            elif event.code == "ABS_RZ":
                throttle["valve"] = event.state
            elif event.code == "BTN_EAST" and event.state == 1:
                action = canactions["setShiftD"]
                msg = can.Message(arbitration_id=action["id"], data=action["data"], extended_id=False)
                bus.send(msg)
            elif event.code == "BTN_SOUTH" and event.state == 1:
                action = canactions["setShiftN"]
                msg = can.Message(arbitration_id=action["id"], data=action["data"], extended_id=False)
                bus.send(msg)
            elif event.code == "BTN_WEST" and event.state == 1:
                action = canactions["setShiftP"]
                msg = can.Message(arbitration_id=action["id"], data=action["data"], extended_id=False)
                bus.send(msg)
            elif event.code == "BTN_NORTH" and event.state == 1:
                action = canactions["setShiftR"]
                msg = can.Message(arbitration_id=action["id"], data=action["data"], extended_id=False)
                bus.send(msg)
            elif event.code == "BTN_DPAD_UP" and event.state == 1:
                data = regularActions["setTemperature"]["data"][3]
                if data < 0x62:
                    regularActions["setTemperature"]["data"][3] += 1
            elif event.code == "BTN_DPAD_DOWN" and event.state == 1:
                data = regularActions["setTemperature"]["data"][3]
                if data > 0x08:
                    regularActions["setTemperature"]["data"][3] -= 1
            elif event.code == "BTN_DPAD_RIGHT" and event.state == 1:
                regularActions["setEVMeter"]["data"][1] += 8
            elif event.code == "BTN_DPAD_LEFT" and event.state == 1:
                data = regularActions["setEVMeter"]["data"][1]
                if data > 7:
                    regularActions["setEVMeter"]["data"][1] -= 8
            else:
                pass

if __name__ == "__main__":
    main()
