import os
import time
import threading
'''today = datatime.data.today()'''
#001使用

def a():
    os.system('sudo python3 /home/pi/001/servicegoogle1.1.py')

    
def b():
    os.system('sudo nginx service start')
    os.system('ffmpeg -i /dev/video0 -f flv rtmp://172.23.121.179:1935/live/test')


point1 = threading.Thread(target = a)
point1.start()
point2 = threading.Thread(target=b)
point2.start()

