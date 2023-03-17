import os
import datetime
import threading

#001使用
def log(title , log):
    '''title輸入標題,log有錯誤訊息打入(無請打入None)'''
    f = open("serverlog.txt" , "a+")
    if log == None:
        f.write(f'{time()}\n Massage:{title}\n')
    else:
        f.write(f'{time()}\n Massage:{title}\n [ERROR] {log}')


def time():
    today=datetime.datetime.today()
    today = today.strftime("time:%Y/%m/%d %H:%M:%S")
    print(today)
    return today
def a():
    os.system('sudo python3 /home/pi/001/servicegoogle1.1.py')

    
def b():
    os.system('sudo nginx service start')
    os.system('ffmpeg -i /dev/video0 -f flv rtmp://172.23.121.179:1935/live/test')

time()


try:
    point1 = threading.Thread(target = a)
    point1.start()
    point2 = threading.Thread(target=b)
    point2.start()
    log('successfully executed', None)
except Exception as e:
    log('Error execute', e)





