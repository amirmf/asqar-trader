import time
import psycopg2

from Terminator import Terminator
from Trader import Trade
import sys

# asqar.py [connector.json] [stg.json] [mode]
from db.DbApi import DataBaseApi

time0 = time.localtime()
time00 = time.time()
print("******************************************")
print("Asqar is starting ...")
connector = "connectors/"+sys.argv[1]
strategy = "strategies/"+sys.argv[2]
mode = sys.argv[3]
print("Connector: " + connector)
print("Strategy: " + strategy)
print("Mode: " + mode)
print("Start time:" + time.strftime("%Y_%m_%d %H:%M:%S", time0))
print("******************************************")




conn = DataBaseApi().getConnection()
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cur.execute("select userid from users where account= '"+sys.argv[1]+"'")
user = cur.fetchall()
if user is not None:
    user = user[0][0]
    t1 = Trade(connector, strategy, mode,conn,user)
    try:
        t1.start()
    finally:
        tr = Terminator(t1.ex, t1.symbol, t1.stgDir, t1.mode)
    time1 = time.localtime()
    time11 = time.time()
    t1.reportAllPos()
    print("##########################################")
    print("Asqar is killing the Trader...")
    print("End time:" + time.strftime("%Y_%m_%d %H:%M:%S", time1))
    print("Total duration:" + str((time11 - time00) / 60 / 60) + " Hour")
    print("Asqar killed the Trader!")
    print("##########################################")
else:
    print(" ########## NO USER Found TO WORK WITH ########## ")