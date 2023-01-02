# import time
#
# t, o, h, l, c, v, df, pu, pd, pc = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
#
#
# def JesusShort(tradeTF, tikP, cn=[]):
#     theBot = {
#         "name": "JesusShort",
#         "desc": "kucoin future timezone +8 2022-1-8 21:45 va 21:50..."
#                 "age candle 0 manfi bud va candele 1,2 mosbat bud "
#                 "va candle 1 qoleye 15 ta candele qabli bud",
#         "doOpen": True,
#         "exitPrice": 0,
#         "dynamicMinProfit": -1,
#         "openCnTime": -1,
#         "newPosPrice": 0,
#         "openType": "sell"
#     }
#
#     doOpen = True
#     for itm in cn[tradeTF]:
#         if cn[tradeTF][1][v] * 120 / 100 >= itm[v] or \
#                 cn[tradeTF][2][v] * 120 / 100 >= itm[v] or \
#                 cn[tradeTF][3][v] * 120 / 100 >= itm[v] or \
#                 cn[tradeTF][4][v] * 120 / 100 >= itm[v]:
#             doOpen = True
#         else:
#             doOpen = False
#             break
#
#     if doOpen:
#         doOpen = (cn[tradeTF][2][df] > 0)
#
#     if doOpen:
#         doOpen = False
#         pctAvg = 0
#         cnter = 0
#         mx = -1000
#         for itm in cn[tradeTF]:
#             mx = max(abs(itm[pc]), mx)
#             pctAvg += abs(itm[pc])
#             cnter += 1
#         pctAvg = (pctAvg - mx) / (cnter - 1)
#         if doOpen:
#             doOpen = mx >= 2 * pctAvg
#
#     if doOpen:
#         for itm in cn[tradeTF]:
#             if cn[tradeTF][2][t] == itm[t]:
#                 continue
#             if cn[tradeTF][2][c] >= itm[c] - 15 and cn[tradeTF][2][c] >= itm[o] - 15:
#                 doOpen = True
#             else:
#                 doOpen = False
#                 break
#     theBot["doOpen"] = doOpen
#     if doOpen:
#         theList = [abs(cn[tradeTF][0][df]), abs(cn[tradeTF][1][df]), abs(cn[tradeTF][2][df]), abs(cn[tradeTF][3][df]),
#                    abs(cn[tradeTF][4][df])]
#         theList.sort(reverse=True)
#         theDif = (theList[0] + theList[2]) / 2 * 80 / 100
#         theBot["dynamicMinProfit"] = theDif * 100 / tikP
#         theBot["openCnTime"] = cn[tradeTF][0][t]
#     return theBot
#
#
# def JesusLong(tradeTF, tikP, cn=[]):
#     theBot = {
#         "name": "JesusLong",
#         "desc": "(REVERSE)kucoin future timezone +8 2022-1-8 21:45 va 21:50..."
#                 "age candle 0 manfi bud va candele 1,2 mosbat bud "
#                 "va candle 1 qoleye 15 ta candele qabli bud",
#         "doOpen": True,
#         "exitPrice": 0,
#         "dynamicMinProfit": -1,
#         "openCnTime": -1,
#         "newPosPrice": 0,
#         "openType": "buy"
#     }
#     doOpen = True
#     for itm in cn[tradeTF]:
#         if cn[tradeTF][1][v] * 120 / 100 >= itm[v] or \
#                 cn[tradeTF][2][v] * 120 / 100 >= itm[v] or \
#                 cn[tradeTF][3][v] * 120 / 100 >= itm[v] or \
#                 cn[tradeTF][4][v] * 120 / 100 >= itm[v]:
#             doOpen = True
#         else:
#             doOpen = False
#             break
#
#     if doOpen:
#         doOpen = (cn[tradeTF][2][df] < 0)
#
#     if doOpen:
#         doOpen = False
#         pctAvg = 0
#         cnter = 0
#         mx = -1000
#         for itm in cn[tradeTF]:
#             mx = max(abs(itm[pc]), mx)
#             pctAvg += abs(itm[pc])
#             cnter += 1
#         pctAvg = (pctAvg - mx) / (cnter - 1)
#         if doOpen:
#             doOpen = mx >= 2 * pctAvg
#
#     if doOpen:
#         for itm in cn[tradeTF]:
#             if cn[tradeTF][2][t] == itm[t]:
#                 continue
#             if cn[tradeTF][2][c] <= itm[c] + 15 and cn[tradeTF][2][c] <= itm[o] + 15:
#                 doOpen = True
#             else:
#                 doOpen = False
#                 break
#     theBot["doOpen"] = doOpen
#     if doOpen:
#         theList = [abs(cn[tradeTF][0][df]), abs(cn[tradeTF][1][df]), abs(cn[tradeTF][2][df]), abs(cn[tradeTF][3][df]),
#                    abs(cn[tradeTF][4][df])]
#         theList.sort(reverse=True)
#         theDif = (theList[0] + theList[2]) / 2 * 80 / 100
#         theBot["dynamicMinProfit"] = theDif * 100 / tikP
#         theBot["openCnTime"] = cn[tradeTF][0][t]
#     return theBot
