import sqlite3
import os
import time

class DataBase:
    def __init__(self, args:bytes, logger, config:dict):
        self.logger = logger.logging()
        self.args = args
        self.config = config
        self.databasefile = f"{config.general['database']['path']}{config.general['database']['name']}"
        self.logger.info(f"Validating the {self.databasefile} data file to continue.")


        if not os.path.exists(self.databasefile):
            self.logger.debug(f"O arquivo {self.databasefile} não existe será necessário criar.")
            conn = sqlite3.connect(self.databasefile)
            cursor = conn.cursor()
        else:
            conn = sqlite3.connect(self.databasefile)
            cursor = conn.cursor()

        cursor.execute('CREATE TABLE IF NOT EXISTS CVE ( id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,'
            'rawid TEXT, date DATE );')

        try:
            conn.commit()
            conn.close()
        except (sqlite3.OperationalError) as e:
            time.sleep(10)
            try:
                conn.commit()
                conn.close()
            except (sqlite3.OperationalError) as e:
                pass

    def compare(self, rawid:str):
        conn = sqlite3.connect(self.databasefile)
        cursor = conn.cursor()
        r = cursor.execute(f"SELECT * FROM CVE WHERE rawid='{rawid}'")
        if len(r.fetchall()) == 0:
            return True
        elif len(r.fetchall()) > 0:
            return False

    def save(self, data:dict):
        conn = sqlite3.connect(self.databasefile)
        cursor = conn.cursor()
        cursor.execute(f"""
        INSERT INTO CVE (rawid, date)
        VALUES ('{data['rawid']}','{data['date']}');
        """)

        try:
            conn.commit()
            conn.close()
            return True
        except (sqlite3.OperationalError) as e:
            time.sleep(10)
            try:
                conn.commit()
                conn.close()
                return True
            except (sqlite3.OperationalError) as e:
                conn.commit()
                conn.close()
                return False
