import OpenOPC
import pywintypes
import time

pywintypes.datetime = pywintypes.TimeType

opc = OpenOPC.client()


def connect_till_success():
    success = False
    while not success:
        try:
            opc.connect("Prosys.OPC.Simulation")
            success = True
        except Exception as ex:
            print("ERROR connect failed")


try:
    connect_till_success()
    while True:
        try:
            opc.read("Static.PsBool1")  # read data and compare values
            print(".", end="")
        except Exception as e:
            print("ERROR ", e)
            connect_till_success()
        time.sleep(1)
finally:
    opc.close()
