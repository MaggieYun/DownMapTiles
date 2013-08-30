#coding=utf-8
#Filename:Dmc_cmd.py
import cmath,urllib,os,math,random,sys,time,threading
# from threading import Condition
import Queue
import datetime

from walkDir import *


class Cdt:
    def __str__(self):
        return '{x = %s,y = %s}'%(self.x,self.y)        

def createName(num,type):
    #'''创建文件夹/文件名称'''
    temp = '00000000'+str(hex(int(num)))[2:]
    return type + temp[::-1][0:8][::-1]

def getPixelFromCdt(x,y,z):
    #'''根据经纬度坐标以及缩放等级获取像素坐标'''
    pixel = Cdt()
    sinLatitude = cmath.sin(y * cmath.pi / 180)
    pixel.x = ((x + 180) / 360) * 256 * (2**z)
    temp = cmath.log((1+sinLatitude)/(1-sinLatitude))
    pixel.y = abs((0.5 - temp / (4 * cmath.pi))*256*(2**z))
    return pixel

def getTileFromPixel(pixel):
    #'''根据像素坐标获取切片'''
    tile = Cdt()
    tile.x = math.floor(pixel.x / 256)
    tile.y = math.floor(pixel.y / 256)
    return tile

def getTileFromCdt(x,y,z):
    #'''根据经纬度坐标以及缩放等级获取切片'''
    return getTileFromPixel(getPixelFromCdt(x,y,z))


   
def createCacheStruc(extent,lvRange,cacheDir):
    #'''创建缓存目录结构及计算tile'''
    global tempTask
    tempTask = Queue.Queue()    #事先把队列创建好之后再创建并启动线程，保证qsize正常

    print u'创建Cache目录及计算tile数目...'

    for lv in lvRange:

        if lv < 10:
            lvName = 'L0' + str(lv)
        else:
            lvName = 'L'+str(lv) 

        startTile = getTileFromCdt(extent[0],extent[1],lv)
        endTile = getTileFromCdt(extent[2],extent[3],lv)
        xRange = range(int(startTile.x),int(endTile.x))
        yRange = range(int(startTile.y),int(endTile.y))
        for row in yRange:
            rowName = cacheDir +os.sep + lvName + os.sep + createName(row,'R') 
            if not os.path.exists(rowName):
                os.makedirs(rowName)  
            
            for col in xRange:
                tempTask.put('%s,%s,%s'%(lv,row,col))


def createRemoteUrl(x,y,z):
    #'''创建远程tile地址'''
    port = str(random.randint(0,3))
    x = str(x)
    y = str(y)
    z = str(z)
    return 'http://mt'+port+'.google.cn/vt/v=w2.115&hl=zh-CN&gl=cn&x='+x+'&s=&y='+y+'&z='+z

def createLocalFile(x,y,z,cacheDir):
    #'''创建缓存本地路径'''
    #计算<等级目录>名称

    if int(z)<10:
        l = 'L0' + str(z)  #x,y,z为字符串类型
    else:
        l = 'L' + str(z)

    #计算<行目录>和<(列)图片>名称
    r = createName(y,'R')
    c = createName(x,'C')
    #拼装本地路径
    return cacheDir + os.sep + l + os.sep + r + os.sep + c + '.png'


def downloadTile(remoteFile,localFile):
    #'''下载远程文件到本地'''
    urllib.urlretrieve(remoteFile,localFile)




def loadTask(task,threadNum):
    global failureTask
    failureTask = []
    global tasksize
    tasksize = tempTask.qsize()

    print u'待下载Tile总计:%s,下载线程数:%s'%(tasksize,threadNum)
    print u'开始下载'
    print u'下载中...'

    for i in range(threadNum):
        tempTask.put(None)
    for i in range(threadNum):
        Download(tempTask).start() #生成多个线程并启动
        print datetime.datetime.now()


    
class Download(threading.Thread):
    progress = 0
    # sucessCount = 0
    failureCount = 0

    def __init__(self,queue):
        threading.Thread.__init__(self)
        self.lock = threading.RLock()
        self.queue = queue

    def run(self):        
        while 1:
            item = self.queue.get()
            if item is None:
                self.queue.task_done()
                break
            valueAry = item.split(",")
            lv = valueAry[0]
            row = valueAry[1]
            col = valueAry[2]
            remoteFile = createRemoteUrl(col,row,lv)
            localFile = createLocalFile(col,row,lv,cacheDir)
            try:
                downloadTile(remoteFile,localFile)
            except:
                logStr = '%s,%s,%s'%(lv,row,col)
                f = file(cacheDir+os.sep+'error.log','a')#在日志文件中打印失败记录
                f.write(logStr+'\n')
                f.close()

                self.lock.acquire()
                Download.failureCount += 1
                print u'下载失败数量：%s'%Download.failureCount #记录下载失败数量
                self.lock.release()

                failureTask.append(logStr)

            
            self.lock.acquire()
            self.queue.task_done()
            Download.progress = Download.progress + 1 #记录下载总数量，包括失败数量
            if Download.progress%100 == 0:
                print u'下载进度为:%s/%s'%(Download.progress,tasksize)
                print datetime.datetime.now()
            self.lock.release()





if __name__ == '__main__':
    
    extent = raw_input(unicode('区域范围:','utf-8').encode('gbk'))
    maxLv = raw_input(unicode('最大等级:','utf-8').encode('gbk'))
    minLv = raw_input(unicode('最小等级:','utf-8').encode('gbk'))

    global extAry,lvRange,cacheDir,threadNum
    ext = [float(i) for i in extent.split(' ')]
    extAry = [ext[0],ext[3],ext[2],ext[1]]          #区域范围
    lvRange = range(int(minLv),int(maxLv) + 1)      #等级范围
    cacheDir = raw_input(unicode('下载目录:','utf-8').encode('gbk'))      #下载目录
    threadNum = raw_input(unicode('下载线程:','utf-8').encode('gbk'))  #下载线程

    databaseDir = raw_input(unicode('请输入sqlite数据库存储目录(eg:c:)：','utf-8').encode('gbk'))
    filename = raw_input(unicode('请为瓦片数据库命名(eg:mytiles)：','utf-8').encode('gbk'))


    # threads = []  #存放所有子线程
    

    createCacheStruc(extAry,lvRange,cacheDir)       #创建缓存目录结构
    loadTask(tempTask,int(threadNum))                    #下载
    
    # print 'over' 

    # import datetime
    # for thread in threads:
    #     thread.join()  #等待线程结束
        # print datetime.datetime.now()

    tempTask.join()
    print u'下载进度为:%s'%Download.progress
    print u'下载结束' 

    print u'正在转换...'
    # print datetime.datetime.now()

    time.sleep(2)
 
    visitDir(cacheDir,databaseDir,filename)



     