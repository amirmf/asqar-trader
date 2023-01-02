import numpy as np
from kucoin_futures.client import Market
import talib

t, o, h, l, c, v, df, pu, pd = 0, 1, 2, 3, 4, 5, 6, 7, 8

def evaShort(tradeTF, tikP, cn=[]):
    theBot = {
        "name": "testShort",
        "desc": "kucoin future timezone +8 2022-1-8 21:45 va 21:50..."
                "age candle 0 manfi bud va candele 1,2 mosbat bud "
                "va candle 1 qoleye 15 ta candele qabli bud",
        "doOpen": True,
        "exitPrice": 0,
        "newPosPrice": 0,
        "openType": "sell"
    }

    doOpen = False
    # newList = cn[tradeTF].copy()
    # newList.reverse()
    # close = np.array(newList)[:, 4]

    #get close data
    a = []
    client = Market(url='https://api-futures.kucoin.com')
    previousTimeStamp = int(cn[tradeTF][0][0]) - (200 * 900000)
    a = client.get_kline_data("XBTUSDTM",'15', previousTimeStamp)
    a.reverse()
    close = np.array(a)[:, 4]
    upper, middle, lower = talib.BBANDS(close, timeperiod=20)

    if (cn[tradeTF][0][c] < cn[tradeTF][0][o]) and (cn[tradeTF][0][o] > upper[19]):
        print("eva did open a pos at " +str(cn[tradeTF][0][t]))
        doOpen = True

    theBot["doOpen"] = doOpen
    if doOpen:
        pass
    return theBot
