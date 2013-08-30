#coding=utf-8
import os,os.path
import Image
import sqlite3
import os
import string,cStringIO

try:
    from sqlite import encode, decode
except ImportError:
    import base64
    sqlite3.encode = base64.encodestring
    sqlite3.decode = base64.decodestring
else:
    sqlite3.encode = encode
    sqlite3.decode = decode

def init_db(path,name):
    '''
    @param path:新建数据库路径
    @param name: 数据库名称 
    @return: 返回新建的数据库
    '''
    conn = sqlite3.connect(path + os.sep + name + ".sqlite")
    c = conn.cursor()
    c.execute('''select count(*) from sqlite_master where type='table' and tbl_name='layer' ''')
    if c.fetchall()[0][0] == 0:
        c.execute('''create table layer (z,x,y,data)''')
    conn.commit()
    c.close()
    return conn

def visitDir(img_path,db_path,db_name):
    conn = init_db(db_path,db_name)
    c = conn.cursor()
    n = 0
    for root,dirs,files in os.walk(img_path):   #遍历文件夹目录，几百万个内存是否会占满？？？效率问题
        for filepath in files:
            try:
                tilepath = os.path.join(root,filepath)
                xyz = tilepath.split(os.sep)
                z = int(xyz[-3][1:])
                y = int(xyz[-2][1:8],16)
                x = int(xyz[-1][1:8],16)
                # print tilepath

                inn = cStringIO.StringIO()
                Image.open(tilepath).save(inn,"png")
                
                sql = "insert into layer (z,x,y,data) values (%d,%d,%d,?)"%(z,x,y)
                c.execute(sql, (sqlite3.Binary(inn.getvalue()),))
                n=n+1
                if n%5000==0:
                    conn.commit()
                    print n 
            except:
                continue
        conn.commit()
    conn.commit()
    c.close() 
    print n 
    print u'地图瓦片已全部成功存入数据库'



if __name__ == '__main__':
    img_path = r'C:\wulumuqi'
    db_path = r'g:'
    db_name = 'ceshishujuku'
    visitDir(img_path,db_path,db_name)