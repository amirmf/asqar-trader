import json
from time import sleep


class Terminator:
    def __init__(self, ex, symbol,config,mode):
        with open(config) as json_data_file:
            initConfig = json.load(json_data_file)
        amount = initConfig["trade"]["amnt"]
        if mode==1 or mode==2: return
        ex.cancel_all_orders(symbol)
        pos= ex.fetch_positions(symbol)
        while len(pos)>0 :
            print("!!!!! ----- ASQAR HAD TO TERMINATE ALL SESSIONS ----- !!!!! ")
            ex.create_order(symbol, 'market',"sell" if pos[0]['entryPrice'] >= pos[0]['liquidationPrice'] else "buy", amount,params={'reduceOnly':True})
            # todo: initconfig amaount
            sleep(9)
            ex.cancel_all_orders(symbol)
            pos = ex.fetch_positions(symbol)
        print("exit terminator")
        tt=""
        tt["JustNeedErorr"]
