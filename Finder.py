import time
from signals import *


def find(stg, tradeTF, tikP, safety, cn):
    theSignal = None
    signalList = stg["signals"]
    signalsRes = []
    for itm in signalList:
        if not itm["active"]:
            continue
        res = eval(itm["src"] + "(tradeTF, tikP, cn)")
        if res is not None:
            cnf = {"conf": itm["conf"]}
            mp = {**res, **cnf}
            if stg["trade"]["profitDynamic"] is True:
                prof=(res["dynamicMinProfit"]-stg["trade"]["fee"])
                if prof > mp["conf"]["minProfit"]:
                    mp["conf"]["minProfit"] = prof
                if prof >= mp["conf"]["profit"]:
                    mp["conf"]["profit"] = prof*2
            signalsRes.append(mp)

    for itm2 in signalsRes:
        if itm2["doOpen"]:
            newPosPrice = tikP
            if itm2["openType"] == "sell":
                newPosPrice = tikP - safety
                # handle price/action for opening position
                # if cn[tradeTF][0][l] - safety * 2 <= newPosPrice:
                #     newPosPrice = cn[tradeTF][0][l] - safety * 2
            if itm2["openType"] == "buy":
                newPosPrice = tikP + safety
                # handle price/action for opening position
                # if cn[tradeTF][0][h] + safety * 2 >= newPosPrice:
                #     newPosPrice = cn[tradeTF][0][h] + safety * 2
            print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ": "
                  + "Trader found signal _(" + itm2["name"] + ")_ at " + str(newPosPrice))
            itm2["newPosPrice"] = newPosPrice
            theSignal = itm2
            break
        else:
            print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ": "
                  + "Trader didn't find _(" + itm2["name"] + ")_ singal")
            theSignal = None
    return theSignal
