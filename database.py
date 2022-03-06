# 作废

import sqlite3

"""
序列号
作品名称
当前价格
预期价格
"""


class database:
    def __init__(self):
        self.con = sqlite3.connect('ubanquan.db')
        self.cursor = self.con.cursor()
        self.creatTable()
        self.con.commit()

    def creatTable(self):
        sql = '''CREATE TABLE IF NOT EXISTS UBANQUAN(
        ID CHAR(20) PRIMARY KEY NOT NULL,
        NAME TEXT NOT NULL,
        PRICE REAL,
        MYPRICE REAL);
        '''
        self.cursor.execute(sql)

    def replace(self, id, name, price, myPrice):
        sql = '''
        REPLACE INTO  UBANQUAN (ID,NAME,PRICE,MYPRICE) VALUES (?,?,?,?)
        '''
        self.cursor.execute(sql, (id, name, price, myPrice,))

    def listAll(self):
        sql = '''SELECT * FROM UBANQUAN'''
        self.cursor.execute(sql)
        result = []
        for raw in self.cursor:
            result += [raw]
        return result

    def getOne(self, id):
        """

        :rtype: object
        """
        sql = '''SELECT * FROM UBANQUAN WHERE ID = ?'''
        self.cursor.execute(sql, (id,))
        return self.cursor.fetchone()

    def close(self):
        self.con.commit()
        self.con.close()

    def setMyPrice(self, discount):
        sql = '''UPDATE UBANQUAN SET MYPRICE=PRICE*?'''
        self.cursor.execute(sql, (discount,))


if __name__ == "__main__":
    db = database()
    db.replace('wwwww', 'dasdasda', 12312, 3213)

    db.close()
