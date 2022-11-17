import atexit
import OpenOPC
import pywintypes
import time

pywintypes.datetime = pywintypes.TimeType

opc = OpenOPC.client()


def shutdown_hook():
    opc.close()
    print("Connection closed")


def connect_till_success():
    success = False
    while not success:
        time.sleep(1)
        try:
            opc.connect("Prosys.OPC.Simulation")
            print("Connection opened")
            success = True
        except Exception as ex1:
            print("ERROR connection failed ", ex1)


# atexit.register(shutdown_hook)
connect_till_success()
while True:
    try:
        opc.read("Static.PsBool1")  # read data and compare values
        print(".", end="")
        time.sleep(1)
    except Exception as ex2:
        print("ERROR reading data ", ex2)
        connect_till_success()
