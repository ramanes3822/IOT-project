import atexit
import json
import logging
import math
import sys
import time
import tracemalloc

import configparser
import win32timezone, datetime
from datetime import datetime

import OpenOPC
import pywintypes
import requests

pywintypes.datetime = pywintypes.TimeType
opc = OpenOPC.client()

# global variable
exit_mode = False
test_mode = False
dictTag = {}
factors = {}
data_dt = {}
mem_data = {}
allTag = []
cmpTag = []
fields = []

crane_id = "ID"

# web configuration
HOST_ADDRESS = "172.21.30.72"
WEB_URL = "http://172.21.30.72/apps/pages/qc.plc.rest&type=wincc"

now = datetime.now()
logFileName = f"app_{now.strftime('%Y%m%d')}.log"
logFileName = fr"logs/{logFileName}"
cfgFileName = r"config/cfgTags.csv"


def start_logger():
    logging.basicConfig(filename=logFileName, filemode="a", format="%(asctime)s-%(message)s", level=logging.INFO, datefmt="%d-%b-%y %H:%M:%S")


def shutdown_hook():
    opc.close()
    print("OPC Server closed")
    logging.info("OPC Server closed")
    exit_mode = True


def read_file(filename):
    content = []
    file = None
    try:
        file = open(filename, "r")
        content = file.readlines()
    except Exception as e:
        logging.error("ERROR reading file %s %s", filename, e)
    finally:
        if file is not None:
            file.close()
    return content


def connect_retry_3():
    count_conn = 1
    success = False
    while not success and count_conn <= 3:
        try:
            if test_mode:
                opc.connect("Prosys.OPC.Simulation")
                # opc.connect("OPCTechs.FujiMicrexNet30DA.3")
            else:
                opc.connect("FUJI_ELECTRIC.MICREX-SX.001")
            success = True
            print("CONNECTED OPC Server")
            logging.info("CONNECTED OPC Server")
        except Exception as ex:
            count_conn = count_conn + 1
            print("ERROR connect failed retry-", count_conn)
            logging.error("ERROR connect failed retry-", count_conn)
            time.sleep(5)


#           if count_conn == 3:
#               exit(-1)


def read_cfg_tag():
    tags = []
    for line in read_file(cfgFileName):
        values = line.strip().split(",")
        key = values[2].strip()
        cmp = values[0].strip()
        dictTag[key] = values[1].strip()
        factors[key] = values[3].strip()
        tags.append(key)
        if cmp == "CMP":
            cmpTag.append(key)
    # print("DICTTAG\n", dictTag)
    # print("FACTORS\n", factors)
    return tags


def read_data():
    total_value = 0.0
    opc_read = opc.read(group="RPS")
    # print("READ\n", opc_read, "\n\n")
    if len(opc_read) == 0:
        print("ERROR READ EMPTY data, RE-CONNECT AGAIN")
        opc.remove("RPS")
        connect_retry_3()
        opc_read = opc.read(tags=allTag, group="RPS", update=500)
    try:
        for data in opc_read:
            (key, val, good, date_time) = data
            mem_data[key] = val
            data_dt[key] = date_time
            if key in cmpTag:
                # print(key, val)
                total_value += float(val)
    except Exception as e:
        print("ERROR READ data ", e)
        logging.error("ERROR READ data %s", e)
        # raise Exception("while reading data. Retry connection")
    # print("MEM\n", mem_data)
    return total_value


def http_put(msg):
    headers = {
        "Accept": "*/*",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json, text/plain",
        "Host": HOST_ADDRESS,
    }
    response = requests.put(WEB_URL, headers=headers, data=msg)
    return response.status_code


def http_send():
    mode = "TEST"
    status_code = "200"
    try:
        for key in mem_data:
            value = str(mem_data[key])
            if factors[key] != "999":
                value = float(factors[key]) * float(value)
            fields.append({"Crane": crane_id, "N": dictTag[key], "V": value, "T": data_dt[key]})
        msg = json.dumps(fields)
        fields.clear()
        if not test_mode:
            mode = "HTTP"
            status_code = http_put(msg)
        print(mode, status_code, msg)
    except Exception as e:
        logging.error("ERROR %s", e)
        logging.error(str(mem_data))


def print_mem():
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")
    logging.info("[ Top 10 ]")
    for stat in top_stats[:10]:
        logging.info(stat)


# main program
# print(sys.argv)
config = configparser.ConfigParser()
config.read(r"config/config.ini")
crane_id = config.get("crane", "crane.id")

if len(sys.argv) == 2 and "test" == str(sys.argv[1]).lower():
    test_mode = True

count_sec = 0
count_mem = 0
value1: float = 0.0
value2: float = 0.0
diff = 0.0
tracemalloc.start()
start_logger()
atexit.register(shutdown_hook)
allTag = read_cfg_tag()
connect_retry_3()
opc.read(tags=allTag, group="RPS", update=500)
while not exit_mode:
    count_sec = 0
    while not exit_mode and count_sec < 60:
        try:
            value1 = read_data()
            mem_data.clear()
            time.sleep(1)
            value2 = read_data()
            diff = math.fabs(value2 - value1)
            print("VALUE DIFFERENCE ", diff)
            if diff > 0.01:
                http_send()
        except Exception as e:
            print("ERROR ", e)
            logging.error("ERROR %s", e)
            connect_retry_3()
        count_sec = count_sec + 1
        count_mem = count_mem + 1
        print("Second", count_sec, "\n")
    # must send in every 60 seconds
    time.sleep(1)
    http_send()
    if count_mem == 3600:
        # print_mem()
        count_mem = 0
# ########################End#####################################
