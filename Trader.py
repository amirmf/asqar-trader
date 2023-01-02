import json
import os
from datetime import datetime
import ccxt
import pandas as pd
import psycopg2
from ccxt import BaseError

import Finder
from BackTestDB import BackTestDB
import time

from Terminator import Terminator
from utils.candleEnum import candle

#TODO: noqate hemayat va moqavemat haye 1 saate ya 1 ruze vurudi bedim ....age qeymat nazdike una bud long nabande ya masalan short nabande
class Trade:
    def __init__(self, connector, strategy, mode, dbCon, user):
        with open(strategy) as json_data_file:
            stg = json.load(json_data_file)
        with open(connector) as json_data_file:
            con = json.load(json_data_file)
        self.ex = ccxt.kucoinfutures({
            "apiKey": con["apiKey"],
            "secret": con["secret"],
            "password": con["password"]
        })

        self.dbCon = dbCon
        self.user = user
        self.strategy = strategy

        self.mode = int(mode)
        self.stg = stg
        self.stgDir = strategy
        self.stgDirFile = strategy.split("/")[-1].split(".json")[0]

        self.symbol = stg["trade"]["symbol"]
        self.checkingSignalTFs = stg["trade"]["checkingSignalTFs"]
        self.tradeTF = stg["trade"]["tradeTF"]
        self.tf = eval(stg["trade"]["tf"])
        self.cnLimitFetch = stg["trade"]["cnLimitFetch"]
        self.fee = stg["trade"]["fee"]
        self.lvg = stg["trade"]["lvg"]
        self.safety = stg["trade"]["safety"]
        self.tCheckOpen = eval(stg["trade"]["tCheckOpen"])
        self.closePosOnNewSignal = stg["trade"]["closePosOnNewSignal"]
        self.amnt = stg["trade"]["amnt"]

        self.skipCnForBackTest = stg["backTest"]["skipCnForBackTest"]
        self.backTestSince = eval(stg["backTest"]["backTestSince"])
        self.backTestToDate = eval(stg["backTest"]["backTestToDate"])

        self.maxProfitUpToNowPct = -100000
        self.tik = 0
        self.ts = None
        self.posC = None
        self.totalProfit = 0
        self.pos = []
        self.isPosBuy = True
        self.profitPct = None
        self.posColumns = ["id", "symbol", "autoDeposit", "maintMarginReq", "riskLimit", "realLeverage", "crossMode",
                           "delevPercentage", "openingTimestamp", "currentTimestamp", "currentQty", "currentCost",
                           "currentComm", "unrealisedCost", "realisedGrossCost", "realisedCost", "isOpen", "markPrice",
                           "markValue", "posCost", "posCross", "posInit", "posComm", "posLoss", "posMargin", "posMaint",
                           "maintMargin", "realisedGrossPnl", "realisedPnl", "unrealisedPnl", "unrealisedPnlPcnt",
                           "unrealisedRoePcnt", "entryPrice", "liquidationPrice", "bankruptPrice", "settleCurrency",
                           "isInverse", "exitPrice", "totalProfit", "maxProfit", "bot"]
        self.signal = None
        self.signalOverride = None
        self.cn = {}
        self.index = self.skipCnForBackTest + 2

        # persist run time - start
        cur = self.dbCon.cursor(cursor_factory=psycopg2.extras.DictCursor)
        insert_script = 'INSERT INTO runner (startts, pair, tf, userid, mode) VALUES (%s,%s,%s,%s,%s)'
        insert_value = (time.time(), self.symbol, self.tf, self.user,self.mode)
        cur.execute(insert_script, insert_value)
        self.dbCon.commit()
        cur.execute("select tradeId from runner order by tradeId DESC LIMIT 1")
        self.runnerId = cur.fetchall()[0][0]
        # persist run time - end

    def start(self):
        if self.mode==1:
            self.startBacktest()
        if self.mode==2:
            self.startBacktest()
        if self.mode==3:
            self.startReal()
        self.reportAllPos()

    def startBacktest(self):
        BackTestDB.fetchData(self, self.symbol, self.checkingSignalTFs, None,
                             self.backTestSince,
                             self.backTestToDate)
        self.mode = 1
        print("===============================================")
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + "(BACKTEST MODE) Trader is awake now...")
        self.filename = "db/trade/backtest/B_"+self.stgDirFile+"_" + self.symbol + "_" + datetime.fromtimestamp(
            self.backTestSince / 1000).strftime(
            "%Y_%m_%d") + "T" + datetime.fromtimestamp(
            self.backTestToDate / 1000).strftime("%Y_%m_%d") + "_" + self.tradeTF + "_" + str(time.time())

        # fill tempCn only for adjusting the sinceTemp with candle time
        tempCn = BackTestDB.loadData(self, self.symbol, self.checkingSignalTFs, 2,
                                     self.backTestSince,
                                     self.backTestToDate, (float(time.time()) * 1000))
        self.backTestSince = tempCn[self.tradeTF][-1][candle.t]

        # skip first 100 candles to be sure we have at least 100 prev candles in bots formula
        sinceTemp = float(self.backTestSince) + (float(self.tf) * self.skipCnForBackTest)


        while sinceTemp <= self.backTestToDate:
            self.ts = float(sinceTemp) + float(
                self.tf) - 1500  # simulate self.fetchTime()...simulate server time with time of candle close minus 1.5Sec
            self.fetchData()
            # simulate the self.fetchTick() start with open price got to high then go back to low and finally go to close
            self.tikP = self.cn[self.tradeTF][0][candle.o]
            step = 7
            doTik = True
            touchHigh = False
            touchLow = False
            touchClose = False
            while doTik:
                self.handleOpenPos()
                if touchClose: break
                if not touchHigh and self.tikP + step < self.cn[self.tradeTF][0][candle.h]:
                    self.tikP += step
                else:
                    touchHigh = True
                if touchHigh and not touchLow and self.tikP - step > self.cn[self.tradeTF][0][candle.l]:
                    self.tikP -= step
                else:
                    touchLow = True
                if touchLow and not touchClose and self.tikP + step < self.cn[self.tradeTF][0][candle.c]:
                    self.tikP += step
                else:
                    touchClose = True
                    self.tikP = self.cn[self.tradeTF][0][candle.c]
            self.tikP = self.cn[self.tradeTF][0][
                candle.c]  # simulate the self.fetchTick() always close price for checking signal
            self.findSignal()
            if self.posC is None:
                if self.signal is not None:
                    self.enterPos()
            else:
                if self.signalOverride is not None:
                    self.handleOpenPos(forceClose=True)
                    self.signal = self.signalOverride
                    self.enterPos()
            sinceTemp += self.tf
            self.index = self.index + 1


    def startForwardTest(self):
        self.mode = 2
        self.filename = "db/trade/forwardtest/F_"+self.stgDirFile+"_" + self.symbol + "_" + datetime.now().strftime(
            "%Y_%m_%d") + "_" + self.tradeTF + "_" + str(time.time())
        self.startTrade()

    def startReal(self):
        self.filename = "db/trade/real/R_"+self.stgDirFile+"_" + self.symbol + "_" + datetime.now().strftime(
            "%Y_%m_%d") + "_" + self.tradeTF + "_" + str(time.time())
        self.mode = 3
        self.startTrade()

    def startTrade(self):
        print("===============================================")
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + "Trader starting...")
        errorCounter = 0
        while True:
            try:
                self.fetchData()
                self.fetchTime()
                self.fetchTick()
                errorCounter = 0
            except BaseError as err:
                print("Got an error on fetching apis..... errorCounter: " + str(errorCounter) + "_" + str(err))
                errorCounter += 1
                if errorCounter < 5:
                    time.sleep(7)
                    continue
                else:
                    Terminator(self.ex, self.symbol,self.stgDir,self.mode)
                    return

            didClose = self.handleOpenPos()
            if didClose: continue

            self.findSignal()
            if self.posC is None:
                if self.signal is not None:
                    self.enterPos()
            else:
                if self.signalOverride is not None:
                    self.handleOpenPos(forceClose=True)
                    self.signal = self.signalOverride
                    self.enterPos()

    def fetchData(self):
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + '->fetchData:')
        if self.mode == 1:
            self.cn = BackTestDB.loadData(self, self.symbol, self.checkingSignalTFs, self.cnLimitFetch,
                                          self.backTestSince,
                                          self.backTestToDate, self.ts)
        elif (self.mode == 2) or (self.mode == 3):
            for itm in self.checkingSignalTFs:
                self.cn[itm] = self.ex.fetch_ohlcv(self.symbol, itm, None, self.cnLimitFetch)
        else:
            print("Invalid Mode*******************")
            return

        for itm2 in self.checkingSignalTFs:
            for itm in self.cn[itm2]:
                diff = itm[candle.c] - itm[candle.o]
                itm.append(diff)
                if diff >= 0:
                    itm.append(itm[candle.h] - itm[candle.c])
                    itm.append(itm[candle.l] - itm[candle.o])
                else:
                    itm.append(itm[candle.h] - itm[candle.o])
                    itm.append(itm[candle.l] - itm[candle.c])
                itm.append(diff*100/itm[candle.o])
            self.cn[itm2].reverse()
        if self.cn[self.tradeTF][0][candle.t] < self.cn[self.tradeTF][1][candle.t]:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("!!!!!!!!!!!!!!!!!!!!!!__ tartibe candle ha qalate __!!!!!!!!!!!!!!!!!!!!!!")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            return

    def handleOpenPos(self,forceClose=False):
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + '->handleOpenPos: forceClose('+str(forceClose)+")")
        exitPriceTemp = 0
        doClose = False

        self.fetchPos()
        if self.posC is not None:
            isPosBuy = self.posC['entryPrice'] >= self.posC['liquidationPrice']
            if isPosBuy:
                exitPriceTemp = self.tikP - self.safety
                self.profitPct = (exitPriceTemp - self.posC['entryPrice']) * 100 / self.posC['entryPrice']
            else:
                exitPriceTemp = self.tikP + self.safety
                self.profitPct = (self.posC['entryPrice'] - exitPriceTemp) * 100 / self.posC['entryPrice']
            self.profitPct -= self.fee
            self.maxProfitUpToNowPct = max(self.maxProfitUpToNowPct, self.profitPct)
            print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": "
                  + "Trader has an open pos with profit:" + str(self.profitPct)[0:5]
                  + "% ("+str(self.profitPct*self.lvg)[0:5]+"%) ["+str(self.lvg)+"]"+"  _   maxProfitUpToNow: " + str(self.maxProfitUpToNowPct)[0:5] + "% ("+str(self.maxProfitUpToNowPct*self.lvg)[0:5]+"%) ["+str(self.lvg)+"]")
            doClose = False
            if 0 < self.profitPct >= self.maxProfitUpToNowPct * self.signal["conf"]["maxProfitUpToNowPctMargin"] / 100 \
                    and self.maxProfitUpToNowPct * 80/100 >= self.profitPct \
                    and self.maxProfitUpToNowPct > self.signal["conf"]["minProfit"]:
                doClose = True
                print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": "
                      + "Trader exit on maxProfitUpToNowPct !!!: " + str(self.profitPct)[0:5]+"%  ("+str(self.profitPct*self.lvg)[0:5]+"%) ["+str(self.lvg)+"]")
            if self.profitPct >= self.signal["conf"]["profit"] or self.profitPct <= self.signal["conf"]["loss"]:
                doClose = True
                print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": "
                      + "Trader exit on SL/TP !!!: " + str(self.profitPct)+"%  ("+str(self.profitPct*self.lvg)[0:5]+"%) ["+str(self.lvg)+"]")
            currentCnCount = 0
            if (self.cn[self.tradeTF][0][candle.t]-self.signal["openCnTime"]) > 0:
                currentCnCount = (self.cn[self.tradeTF][0][candle.t] - self.signal["openCnTime"]) / self.tf
            if 0 < self.signal["conf"]["deadlineCnCount"] <= currentCnCount and 0 > self.profitPct <= self.signal["conf"]["loss"]/4:
                doClose = True
                print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": "
                      + "Trader exit on deadlineCnCount ###: " + str(self.profitPct)+"%  ("+str(self.profitPct*self.lvg)[0:5]+"%) ["+str(self.lvg)+"]")
            if doClose or forceClose:
                self.signal["exitPrice"] = exitPriceTemp
                self.exitPos()
            if self.mode == 3:
                time.sleep(3.7)
        return doClose

    def findSignal(self):
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + '->findSignal:')
        self.signalOverride=None
        if self.posC is not None:
            if not self.closePosOnNewSignal:
                print("Skip finding signal because we have an open position (closePosOnNewSignal is FALSE)")
                return
            else:
                print("do findSignal while having open position (closePosOnNewSignal is TRUE)")

        if self.ts < self.cn[self.tradeTF][0][candle.t] + self.tf - self.tCheckOpen and self.mode != 1:
            if self.posC is not None:
                return
            print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": "
                  + "Trader is waiting for candle close to check condition(sec:" + str(
                (self.cn[self.tradeTF][0][candle.t] + self.tf - self.tCheckOpen - self.ts) / 1000) + ")")
            time.sleep((self.cn[self.tradeTF][0][candle.t] + self.tf - self.tCheckOpen - self.ts) / 1000)
            return
        if self.posC is not None and self.closePosOnNewSignal:
            self.signalOverride = Finder.find(self.stg,self.tradeTF, self.tikP, self.safety, self.cn)
            if self.signalOverride is not None:
                print("Found signalOverride...")
        else:
            self.signal = Finder.find(self.stg,self.tradeTF, self.tikP, self.safety, self.cn)

    def fetchTime(self):
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + '->fetchTime:')
        if (self.mode == 3) or (self.mode == 2):
            self.ts = self.ex.fetch_time()
        elif self.mode == 1:
            pass
        else:
            print("Invalid Mode*******************")
            return

    def enterPos(self):
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + '->enterPos:')
        self.maxProfitUpToNowPct=-10000
        if self.mode == 3:
            self.cancelAllOrders()
            try:
                self.ex.create_order(self.symbol, 'limit', self.signal["openType"], self.amnt,
                                     self.signal["newPosPrice"],
                                     {'leverage': self.lvg})
                print("Wait for enter order to fulfill(9sec)")
                time.sleep(9)
                self.cancelAllOrders()
            except BaseError as err:
                print(
                    "!!!!!!!!!!! ----- ERR ----- : someThing went wrong while creating enter order : " + str(err))
                Terminator(self.ex, self.symbol,self.stgDir,self.mode)
            self.fetchPos()
        elif (self.mode == 1) or (self.mode == 2):
            self.posC = {
                "id": self.ts,
                "symbol": self.symbol,
                "autoDeposit": False,
                "maintMarginReq": -1,
                "riskLimit": -1,
                "realLeverage": self.lvg,
                "crossMode": -1,
                "delevPercentage": -1,
                "openingTimestamp": -1,
                "currentTimestamp": -1,
                "currentQty": -1,
                "currentCost": -1,
                "currentComm": -1,
                "unrealisedCost": -1,
                "realisedGrossCost": -1,
                "realisedCost": -1,
                "isOpen": True,
                "markPrice": -1,
                "markValue": -1,
                "posCost": -1,
                "posCross": -1,
                "posInit": -1,
                "posComm": -1,
                "posLoss": -1,
                "posMargin": -1,
                "posMaint": -1,
                "maintMargin": -1,
                "realisedGrossPnl": -1,
                "realisedPnl": -1,
                "unrealisedPnl": -1,
                "unrealisedPnlPcnt": -1,
                "unrealisedRoePcnt": -1,
                "entryPrice": self.signal["newPosPrice"],
                "liquidationPrice": self.signal["newPosPrice"] + 10000 if self.signal["openType"] == "sell" else
                self.signal["newPosPrice"] - 10000,
                "bankruptPrice": -1,
                "settleCurrency": "USDT",
                "isInverse": False,
                "exitPrice": -1,
                "totalProfit": 0,
                "maxProfit": -1000,
                "bot": self.signal["name"]
            }
            self.pos = [self.posC]
        else:
            print("Invalid Mode*******************")
            return
        self.persistEnterPos()

    def exitPos(self):
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + '->exitPos:')
        self.posC["isOpen"] = False
        self.posC["realisedPnl"] = self.profitPct * self.posC["entryPrice"]
        self.posC["unrealisedPnl"] = self.posC["realisedPnl"]
        self.posC["unrealisedPnlPcnt"] = self.profitPct
        self.posC["maxProfit"] = self.maxProfitUpToNowPct
        self.posC["exitPrice"] = self.signal["exitPrice"]
        self.totalProfit += self.posC["unrealisedPnlPcnt"]
        self.posC["totalProfit"] = self.totalProfit
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + "Trader total profit up to now: " + str(
            self.posC["totalProfit"]) + "%")
        self.pos = [self.posC]
        if self.mode == 3:
            try:
                self.ex.create_order(self.symbol, 'limit', ("sell" if self.signal["openType"] == "buy" else "buy"),
                                     self.amnt,
                                     self.posC["exitPrice"], {'leverage': self.lvg,'reduceOnly':True})
                print("Wait for exit order to fulfill(9sec)")
                time.sleep(9)
                tmpPos = self.ex.fetch_positions(self.symbol)
                if len(tmpPos) > 0:
                    return

            except BaseError as err:
                print("!!!!!!!!!!! ----- ERR ----- : someThing went wrong while creating exit order : " + str(err))
                Terminator(self.ex, self.symbol,self.stgDir,self.mode)
        elif self.mode == 2:
            pass
        elif self.mode == 1:
            pass
        else:
            print("Invalid Mode*******************")
            return
        self.maxProfitUpToNowPct = -100000
        self.persistExitPos()
        return 4.2

    def persistEnterPos(self):
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + '->persistEnterPos:')
        if self.posC is None:
            return
        positionType = None
        strategy = self.strategy.split("/", 1)[1]
        if (self.posC['entryPrice'] >= self.posC['liquidationPrice']):
            positionType = "long"
        else:
            positionType = "SHORT"
        if self.mode==1 or self.mode==2:
            insert_value = (self.posC['id'],
                            self.user,
                            self.runnerId,
                            self.tf,
                            self.ts,
                            self.cn[self.tradeTF][0][candle.t],
                            positionType,
                            "open",
                            self.signal['name'],
                            strategy,
                            self.lvg,
                            self.posC['entryPrice'],
                            self.fee,
                            self.maxProfitUpToNowPct,
                            None,
                            None,
                            self.amnt)
        elif self.mode == 3:
            insert_value = (self.posC['info']['id'],
                            self.user,
                            self.runnerId,
                            self.tf,
                            self.ts,
                            self.cn[self.tradeTF][0][candle.t],
                            positionType,
                            "open",
                            self.signal['name'],
                            strategy,
                            self.lvg,
                            self.posC['entryPrice'],
                            self.fee,
                            self.maxProfitUpToNowPct,
                            None,
                            None,
                            self.amnt)
        # persist Enter pos - start
        cur = self.dbCon.cursor(cursor_factory=psycopg2.extras.DictCursor)
        insert_script = 'INSERT INTO orders(orderid,userid,tradeid,timeframe,entertime,candletime,positiontype,tradetype,signal,startegy,leverage,price,fee,maxprofit,maxloss,totalpnl,amount) ' \
                        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        cur.execute(insert_script, insert_value)
        self.dbCon.commit()


    def cancelAllOrders(self):
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + '->cancelAllOrders:')
        if self.mode == 3:
            try:
                self.ex.cancel_all_orders(self.symbol)
            except BaseError as err:
                print(
                    "!!!!!!!!!!! ----- ERR ----- : someThing went wrong while creating exit order : " + str(err))
                Terminator(self.ex, self.symbol,self.stgDir,self.mode)
        elif self.mode == 2:
            pass
        elif self.mode == 1:
            pass
        else:
            print("Invalid Mode*******************")
            return

    def persistExitPos(self):
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + '->persistExitPos:')
        # if self.posC is None:
        #     return
        # df = pd.DataFrame([list(self.posC.values())])
        #
        #
        if self.posC is None:
            return
        # df = pd.DataFrame([list(self.posC.values())])
        # headers = False
        # if os.path.exists('%s.csv' % self.filename):
        #     headers = False
        # else:
        #     headers = True

        positionType = None
        strategy = self.strategy.split("/", 1)[1]
        if (self.posC['entryPrice'] >= self.posC['liquidationPrice']):
            positionType = "long"
        else:
            positionType = "SHORT"

        if self.mode==1 or self.mode==2:
            insert_value = (self.posC['id'],
                            self.user,
                            self.runnerId,
                            self.tf,
                            self.ts,
                            self.cn[self.tradeTF][0][candle.t],
                            positionType,
                            "exit",
                            self.signal['name'],
                            strategy,
                            self.lvg,
                            self.posC['exitPrice'],
                            self.fee,
                            self.maxProfitUpToNowPct,
                            None,
                            self.posC['unrealisedPnlPcnt'],
                            self.amnt)
        elif self.mode == 3 :
            insert_value = (self.posC['info']['id'],
                            self.user,
                            self.runnerId,
                            self.tf,
                            self.ts,
                            self.cn[self.tradeTF][0][candle.t],
                            positionType,
                            "exit",
                            self.signal['name'],
                            strategy,
                            self.lvg,
                            self.posC['entryPrice'],
                            self.fee,
                            self.maxProfitUpToNowPct,
                            None,
                            self.posC['unrealisedPnlPcnt'],
                            self.amnt)

        # persist Exit pos - start
        cur = self.dbCon.cursor(cursor_factory=psycopg2.extras.DictCursor)
        insert_script = 'INSERT INTO orders(orderid,userid,tradeid,timeframe,entertime,candletime,positiontype,tradetype,signal,startegy,leverage,price,fee,maxprofit,maxloss,totalpnl,amount) ' \
                        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        cur.execute(insert_script, insert_value)
        self.dbCon.commit()
        # persist Exit pos - end

        self.pos = []
        self.posC = None
        self.signal = None


    def fetchTick(self):
        print(time.strftime("%Y_%m_%d %H:%M:%S", time.localtime()) + ": " + '->fetchTick:')
        if (self.mode == 3) or (self.mode == 2):
            self.tik = self.ex.fetch_ticker(self.symbol)
            self.tikP = self.tik['last']
        elif self.mode == 1:
            self.tik = self.ex.fetch_ticker(self.symbol)
            self.tikP = self.tik['last']
        else:
            print("Invalid Mode*******************")
            return

    def fetchPos(self):
        if self.mode == 3:
            self.posC = None
            self.pos = []
            self.isPosBuy = True
            self.profitPct = None
            try:
                self.pos = self.ex.fetch_positions(self.symbol)
                if len(self.pos) > 0:
                    self.posC = self.pos[0]
            except BaseError as err:
                print("!!!!!!!!!!! ----- ERR ----- : someThing went wrong while fetching open positions : " + str(
                    err))
                Terminator(self.ex, self.symbol,self.stgDir,self.mode)
        elif self.mode == 2:
            # we already have open position in posC object cuz we filled it in enterPos method most certainly
            pass
        elif self.mode == 1:
            # we already have open position in posC object cuz we filled it in enterPos method most certainly
            pass
        else:
            print("Invalid Mode*******************")
            return

    def reportAllPos(self):
        cur = self.dbCon.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select * from orders where tradeid = " + str(self.runnerId)+" order by id")
        posReportList = cur.fetchall()

        print('______________________________________________________________________________________')
        print('______________________________report all position(' + str(len(posReportList)) + ')__________________________________')
        print('______________________________________________________________________________________')
        cnter =0
        for itm in posReportList:
            if itm[8] == "exit":
                print("t:" + str(datetime.utcfromtimestamp(itm[6] / 1000)) +
                      ", en:" + str(posReportList[cnter-1][12]) +
                      ", ex:" + str(itm[12]) +
                      ", " + str(itm[7]) +
                      ", (" + str(itm[16])[0:4] + "% = "+str(itm[16]*itm[11])[0:5]+"%) ["+str(itm[11])+"]"+
                      ", bot:" + str(itm[9])
                      )
            cnter +=1
        print("")
        print('Total profit'+"(" + str(self.totalProfit)[0:4] + "% = "+str(self.totalProfit*self.lvg)[0:6]+"%) ["+str(self.lvg)+"]")
        print('______________________________________________________________________________________')
        print('______________________________________________________________________________________')
