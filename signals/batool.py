import time
t, o, h, l, c, v, df, pu, pd = 0, 1, 2, 3, 4, 5, 6, 7, 8

def BatoolLong(tradeTF, tikP, cn=[]):
    theBot = {
        "name": "BatoolLong",
        "desc": "ye candele manfiye kuchulu ke bade dota candle e mosbat umade bashe va qable yek candle mosbate dg",
        "doOpen": True,
        "exitPrice": 0,
        "newPosPrice": 0,
        "openType": "buy"
    }
    doOpen = True

    doOpen = cn[tradeTF][1][df] <= 0 and cn[tradeTF][3][df] > 0 and cn[tradeTF][2][df] > 0 and cn[tradeTF][0][df] > 0
    if doOpen:
        doOpen =  abs(cn[tradeTF][0][df]) > abs(cn[tradeTF][1][df]) < abs(cn[tradeTF][2][df])
    if doOpen:
        doOpen =  abs(cn[tradeTF][0][v]) > abs(cn[tradeTF][1][v]) < abs(cn[tradeTF][2][v])

    theBot["doOpen"] = doOpen
    if doOpen:
        pass
    return theBot
