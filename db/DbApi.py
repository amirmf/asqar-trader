import json
import psycopg2
import psycopg2.extras

class DataBaseApi:
    def getConnection(self):
        self.conn = None
        if self.conn is None:
            try:
                with open("db/connectionString.json") as json_data_file:
                    dbPropertie = json.load(json_data_file)
                self.conn = psycopg2.connect(
                    host=dbPropertie["hostname"],
                    dbname=dbPropertie["database"],
                    user=dbPropertie["username"],
                    password=dbPropertie["passw"],
                    port=dbPropertie["port_id"]
                )
                print("----- Trader connected to postqres Database with conn =  -----" + str(self.conn))
                return self.conn
            except Exception as error:
                print("----- Trader could'nt connect to postgres DB because " + error)
            # finally:
            #     if self.conn is not None:
            #         self.conn.close()
        else:
            return self.cur