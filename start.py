import os
import datetime
import threading

#001使用
def log(title , log):
    '''title輸入標題,log有錯誤訊息打入(無請打入None)'''
    with open("serverlog.txt" , "a+") as f:
        if log == None:
            f.write(f'{time()}\nMassage:{title}\n ------------------------------\n')
        else:
            f.write(f'{time()}\n Massage:{title}\n [ERROR] {log}\n------------------------------\n')


def time():
    today=datetime.datetime.today()
    today = today.strftime("Time:%Y/%m/%d %H:%M:%S")
    print(today)
    return today
def a():
    try:
        os.system('sudo python3 /home/pi/001/servicegoogle1.1.py')
    except:
        log('開啟servicegoogle1.1.py錯誤', e)
    
def b():
    try:
        os.system('sudo nginx service start')
        os.system('ffmpeg -i /dev/video0 -f flv rtmp://172.23.121.179:1935/live/test')
    except:
        log('影像串流發生問題', e)
log('successfully executed', None)

try:
    point1 = threading.Thread(target = a)
    point1.start()
    point2 = threading.Thread(target=b)
    point2.start()
    log('successfully executed', None)
except Exception as e:
    log('Error execute', e)





