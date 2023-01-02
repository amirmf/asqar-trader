import os
from datetime import datetime
import pandas as pd
from kucoin_futures.client import Market
from utils.tfMap import tfMap

class BackTestDB:

    def fetchData(self, symbol, checkingSignalTFs, limit, since, toDate):
        client = Market(url='https://api-futures.kucoin.com')
        for itm in checkingSignalTFs:
            timeframe = itm
            filename = "db/backdb/"+symbol+"_"+datetime.fromtimestamp(since / 1000).strftime("%Y_%m_%d") + "T" + datetime.fromtimestamp(
                toDate / 1000).strftime("%Y_%m_%d")+ "_"+ timeframe
            cn= []
            tempSince = since
            if os.path.exists('%s.csv' % filename) is False:
                while (tempSince <= toDate):
                    cn.extend(client.get_kline_data(symbol,tfMap.array[timeframe], tempSince))
                    tempSince = cn[len(cn)-1][0]  #last row's timeStamp
                df = pd.DataFrame(cn)
                df.columns=['t', 'o', 'h', 'l', 'c', 'v']
                df.to_csv('%s.csv' % filename, mode='a', index=False)
            else:
                print("file already exist !!!!!!!!!!!!!!!!!!!!!!!!!")

    def loadData(self, symbol, checkingSignalTFs, limit, since, toDate, currentTS):
        cn={}
        for itm in checkingSignalTFs:
            timeframe = itm
            cn[timeframe]=[]
            filename = "db/backdb/"+symbol+"_"+datetime.fromtimestamp(since / 1000).strftime("%Y_%m_%d") + "T" + datetime.fromtimestamp(
                toDate / 1000).strftime("%Y_%m_%d") + "_" + timeframe

            #cn[timeframe] = pd.read_csv(filename+".csv").sort_values(by='t',ascending=True).to_numpy().tolist()

            cn[timeframe] = pd.read_csv("db/backdb/XBTUSDTM_2021_10_02T2022_02_04_15m.csv").sort_values(by='t', ascending=True).query(
                "t<" + str(currentTS)).to_numpy().tolist()
            if limit!=2:
                cn[timeframe].reverse()
            cn[timeframe]=cn[timeframe][0:limit]
            cn[timeframe].reverse()
        return cn