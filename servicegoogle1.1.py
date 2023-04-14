# encoding:utf-8
from pymavlink import mavutil
import os
import time
from dronekit import connect, VehicleMode, LocationGlobalRelative
from EH10_cmd_control import Gimbal
from Scripts.sql_server.SQLS import sqlserver
import threading , json
import datetime
from cryptography.fernet import Fernet

global yaw, pitch
# 主程式

print('伺服器端開啟')
while True:
    try:
        vehicle = connect('/dev/ttyAMA0', baud=921600,
                          wait_ready=True)  # 無人機與樹莓派連線
        print('無人機與樹莓派連接成功')
        break
    except:
        time.sleep(1)

# encoding:utf-8
EH10 = Gimbal("/dev/ttyUSB0", 115200)
print('畫面與樹莓派連接成功')
EH10.set_return_head_cmd()

# 從下複製貼上

with open('encrypted.txt', 'rb') as f:
    key = f.read()
fernet = Fernet(key)

with open('info.json', 'rb') as f:
    encrypted_data = f.read()
# 解密 JSON
decrypted_data = fernet.decrypt(encrypted_data).decode()
data = json.loads(decrypted_data)



head = ''
pitch = 0
yaw = 0

ID = data['drone_id']  # 無人機編號


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


def takeoff(height):
    while True:
        head = vehicle.heading
        print(height)
        # 有無gps fix 濾波器
        # 無gps無法啟動
        server.sql_update(ID, 'takeoff', '')
        i = 0
        send('1')
        while not vehicle.is_armable:
            time.sleep(1)
            i = i+1
            if i >= 5:
                send("2")
                break
        if float(vehicle.battery.voltage) < 11.5:
            print('低電壓')
            send("3")
            break
        print('設定模式： GUIDED')
        vehicle.mode = VehicleMode("GUIDED")
        time.sleep(1)
        vehicle.armed = True
        i = 0
        while not vehicle.armed:
            print("等待解鎖...")
            time.sleep(1)
            i = i+1
            if i >= 5:
                print('無法解鎖')
                send("4")
                break
        if i == 5:
            server.sql_update(ID, 'dronemode', '2')
            break
        send('5')
        time.sleep(3)
        vehicle.simple_takeoff(height)
        while True:
            time.sleep(1)
            print("目前高度：", vehicle.location.global_relative_frame.alt)
            status(False , 3)
            if float(vehicle.location.global_relative_frame.alt) >= float(height)*0.95:
                break
        server.sql_update(ID, 'dronemode', '1')
        send('6')
        break
    return head


def updown(ud):
    server.sql_update(ID, 'up_down', '')
    alt = int(vehicle.location.global_relative_frame.alt)
    if not alt+2 > int(ud) > alt-2:
        server.sql_update(ID, 'dronemode', '3')
        lat = vehicle.location.global_relative_frame.lat
        lon = vehicle.location.global_relative_frame.lon
        vehicle.simple_goto(LocationGlobalRelative(lat, lon, int(ud)))
        while True:
            time.sleep(1)
            print("目前高度：", vehicle.location.global_relative_frame.alt)
            status(False , 3) 
            if float(ud)*1.02 >= float(vehicle.location.global_relative_frame.alt) >= float(ud)*0.98:
                break
        server.sql_update(ID, 'dronemode', '1')
        send('6')
    else:
        send('7')


def land(head):
    print("即將降落")
    send('8')
    '''try:
        condition_yaw(head, False)
        while vehicle.heading != head:
            if head-5 <= vehicle.heading <= head+5:
                break
            else: 
                time.sleep(1)
                print('延遲中')
    except:
        pass'''
    vehicle.parameters['RTL_ALT'] = 0
    vehicle.mode = VehicleMode("RTL")
    while vehicle.armed:
        gps0 = "%s" % vehicle.gps_0
        try:
            status(False , 3)
        except:
            pass
        print('返回中')
        time.sleep(1)

    try:
        server.sql_update(ID, 'dronemode', '2')
        server.sql_update(ID, 'land', '')
    except:
        pass
    send('6')
    vehicle.mode = VehicleMode("GUIDED")


def send(txt):
    try:
        server.sql_update(ID, 'massage', txt)
    except:
        pass


def condition_yaw(heading, relative):
    heading = int(heading)
    if relative:
        isRelative = 1
        if heading < 0:
            direction = -1
            heading = abs(heading)
        else:
            direction = 1
    else:
        isRelative = 0
        if heading < 180:
            direction = -1
        else:
            direction = 1

    if not relative:
        direction = 0
    # 生成CONDITION_YAW命令
    msg = vehicle.message_factory.command_long_encode(
        0, 0,       # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
        0,          # confirmation
        heading,    # param 1, yaw in degrees
        7,          # param 2, yaw speed
        direction,  # param 3, direction
                    isRelative,  # param 4, relative or absolute degrees
        0, 0, 0)    # param 5-7, not used
    # 发送指令
    vehicle.send_mavlink(msg)
    vehicle.flush()
    server.sql_update(ID, 'droneturn', '')
    send('6')
    time.sleep(1)


def status(info , row):
    '''status(info , row)輸輸入:true or flase(是否要進行低電壓檢測) , 目前模式
    return 高度，電壓，經緯度
    作用:監測低電壓，高度 電量 gps上傳到sql'''
    if info == True:
        if float(vehicle.battery.voltage) < 21.3 and row == 1:
            print('低電壓')
            try:
                send("9")
            except:
                pass
            land(head)

    server.sql_update(ID, 'alt', vehicle.location.global_relative_frame.alt)
    server.sql_update(ID, 'dronebatt', vehicle.battery.voltage)
    gps0 = "%s" % vehicle.gps_0
    server.sql_update(ID, 'GPSInfo', str(gps0))
    gps = str(vehicle.location.global_relative_frame.lat) + \
        ',' + str(vehicle.location.global_relative_frame.lon)
    server.sql_update(ID, 'lat_lon', gps)

    return vehicle.location.global_relative_frame.alt, vehicle.battery.voltage, gps


def send_body_ned_velocity(velocity_x, velocity_y, velocity_z, duration):
    if int(duration) < 0:
        if velocity_x != 0:
            velocity_x = velocity_x*-1
        if velocity_y != 0:
            velocity_y = velocity_y*-1
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        # frame Needs to be MAV_FRAME_BODY_NED for forward/back left/right control.
        mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED, #自身位置
        0b0000101111000111,  # type_mask
        0, 0, 0,  # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z,  # m/s
        0, 0, 0,  # x, y, z acceleration
        0, 0)
    x=0
    while x <= abs(duration):
        vehicle.send_mavlink(msg)
        vehicle.flush()
        time.sleep(1)
        x = x+1
    server.sql_update(ID, 'forward_back', '')
    print('完成')
    send('6')

def send_local_ned_velocity(vx, vy, vz):
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,0,0,mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b110111000111,
        0,0,0,
        vx,vy,vz,
        0,0,0,
        0,0)
    vehicle.send_mavlink(msg)
    vehicle.flush()



def cam_control(cam):
    '''置中'0'向右'1'向左'2'向上'3'向下"4"'''
    # control Mode:MODE_ANGLE_REF_FRAME
    # pitch angle: 正值向下，負值向上
    # yaw angle:   正值向右，負值向左
    # 雲台上下左右控制皆設定，以每秒50度旋轉18度
    # 旭展編輯撰寫
    global yaw, pitch
    cam = str(cam)
    if cam == '0':
        EH10.set_return_head_cmd()
        EH10.set_camera_zoomOut_cmd()     # camera zoom in
        pitch = 0
        yaw = 0
        time.sleep(3)
        EH10.set_camera_stop_zoom_cmd()
    if cam == '1':
        yaw = yaw+4
    if cam == '2':
        yaw = yaw-4
    if cam == '3':
        pitch = pitch-4
    if cam == '4':
        pitch = pitch+4
    if cam == '5':
        EH10.set_camera_zoomIn_cmd()     # camera zoom in
        time.sleep(0.66)
        EH10.set_camera_stop_zoom_cmd()  # camera stop zoom
    if cam == '6':
        EH10.set_camera_zoomOut_cmd()     # camera zoom in
        time.sleep(0.66)
        EH10.set_camera_stop_zoom_cmd()  # camera stop zoom
    if cam != '0':
        EH10.set_movement_cmd(0, 5, 5, 0, 0, 50, pitch, 50, yaw)
    server.sql_update(ID, 'cam', '')

    print('完成')
    send('0')


def allmove(ms1, ma2, ma3):
    if ms1 != '0':
        send_body_ned_velocity(1, 0, 0, int(ms1))
        time.sleep(2)
    if ma2 != '0':
        send_body_ned_velocity(0, 1, 0, int(ma2))
        time.sleep(2)
    if ma3 != '0':
        condition_yaw(int(ma3), True)

    server.sql_update(ID, 'allmove_FW', '')
    server.sql_update(ID, 'allmove_LR', '')
    server.sql_update(ID, 'allmove_yaw', '')
    send("6")

def connect_status_thread():
    server = sqlserver("test", '00000000')
    while True:
        try:
            server.sql_update(ID, 'connect_status', 'true')
            time.sleep(1)
        except Exception as e:
            print(e)
            
# ---------建立連線---------
server = sqlserver(data['sql_account'], data['sql_password'])
if vehicle.armed != True:
    server.sql_init(ID)
    print('重置成功')
else:
    print('起飛中無法重置')

thread_connect_status = threading.Thread(target=connect_status_thread, daemon=True)
thread_connect_status.start()

a = 0
server_connect_num = 0

while True:
    try:
        row = server.sql_listen(ID)
        alt, bat, gps = status(True , row[5])
        print(row)
        if not vehicle.armed:
            server.sql_update(ID, 'dronemode', 2)
        if row[1] != None:
            server.sql_update(ID, 'dronemode', 3)
            head = takeoff(row[1])
        if row[2] != None:
            server.sql_update(ID, 'dronemode', 3)
            land(head)
        if row[6] != None:
            updown(row[6])
        if row[8] != None:
            condition_yaw(int(row[8]), True)
        print(head, vehicle.heading)
        if row[9] != None:
            send_body_ned_velocity(1, 0, 0, int(row[9]))
            server.sql_update(ID, 'forward_back', '')
        if row[14] != None and row[15] != None and row[16] != None:
            allmove(row[14], row[15], row[16])
        if row[11] != None:
            cam_control(row[11])
        print(pitch,yaw)
        "EH10.set_movement_cmd(0, 5, 5, 0, 0, 50, pitch, 50, yaw)"
        time.sleep(1)
    except:
        time.sleep(1)
