import os
import datetime
import threading
import time
from cryptography.fernet import Fernet
import json

#001使用
with open('/home/pi/RCCS-raspberry/encrypted.txt', 'rb') as f:
    key = f.read()
fernet = Fernet(key)

with open('/home/pi/RCCS-raspberry/info.json', 'rb') as f:
    encrypted_data = f.read()
# 解密 JSON
decrypted_data = fernet.decrypt(encrypted_data).decode()
data = json.loads(decrypted_data)

def log(title , info):
    '''title輸入標題,log有錯誤訊息打入(無請打入None)'''
    today=datetime.datetime.today()
    todaytime = today.strftime("Time:%Y/%m/%d %H:%M:%S")
    today = today.strftime("%Y_%m_%d")
    path=(f'/home/pi/RCCS-raspberry/log/raspberry_server_log{today}.txt')
    with open(path , "a+") as f:
        if info == None:
            f.write(f'{todaytime}\nMassage:{title}\n ------------------------------\n')
        else:
            f.write(f'{todaytime}\nMassage:{title}\n [ERROR] {info}\n------------------------------\n')

def a():
    try:
        os.system('sudo python3 /home/pi/RCCS-raspberry/servicegoogle1.1.py')
    except:
        log('開啟servicegoogle1.1.py錯誤', e)
    
def b():
    try:
        os.system('sudo nginx service start')
        os.system('sudo /usr/local/nginx/sbin/nginx')
        time.sleep(1)
        ip = data['zerotier_ip_address']
        os.system(f'ffmpeg -re -i  /dev/video0 -f flv rtmp://{ip}:1935/live/test')
    except:

        log('影像串流發生問題', e)

try:
    point1 = threading.Thread(target = a)
    point1.start()
    point2 = threading.Thread(target=b)
    point2.start()
    log('successfully executed', None)
except Exception as e:
    log('Error execute', e)





