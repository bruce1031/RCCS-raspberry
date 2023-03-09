# encoding:utf-8
from pymavlink import mavutil
import pygsheets
import os
import time
from dronekit import connect, VehicleMode, LocationGlobalRelative
from EH10_cmd_control import Gimbal
from Scripts.sql_server.SQLS import sqlserver
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

head = ''
gpsnow = ''

pitch = 0
yaw = 0

ID = 1  # 無人機編號


def takeoff(height):
    while True:
        head = vehicle.heading
        print(height)
        gpsnow = str(vehicle.location.global_relative_frame.lat) + \
            ',' + str(vehicle.location.global_relative_frame.lon)
        # 有無gps fix 濾波器
        # 無gps無法啟動
        server.sql_update(ID, 'takeoff', '')
        i = 0
        send('啟動起飛前檢查程序')
        while not vehicle.is_armable:
            time.sleep(1)
            i = i+1
            if i >= 5:
                send("起飛前檢查錯誤,請查看您的gps、fix、濾波器")
                break
        if float(vehicle.battery.voltage) < 11.5:
            print('低電壓')
            send("低電壓、不建議起飛")
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
                send("無法解鎖")
                break
        if i == 5:
            server.sql_update(ID, 'dronemode', '2')
            break
        send('起飛')
        vehicle.simple_takeoff(height)
        while True:
            time.sleep(1)
            print("目前高度：", vehicle.location.global_relative_frame.alt)
            status()
            if float(vehicle.location.global_relative_frame.alt) >= float(height)*0.95:
                break
        server.sql_update(ID, 'dronemode', '1')
        send('完成')
        break
    return head, gpsnow


def close(height):
    while True:
        time.sleep(1)
        print("目前高度：", vehicle.location.global_relative_frame.alt)
        if float(vehicle.location.global_relative_frame.alt) >= float(height)*0.95:
            time.sleep(1)
            break
    server.sql_update(ID, 'dronemode', '1')
    send('完成')


def updown(ud):
    server.sql_update(ID, 'up_down', '')
    time.sleep(1)
    alt = int(vehicle.location.global_relative_frame.alt)
    if not alt+2 > int(ud) > alt-2:
        server.sql_update(ID, 'dronemode', '3')
        time.sleep(1)
        lat = vehicle.location.global_relative_frame.lat
        lon = vehicle.location.global_relative_frame.lon
        vehicle.simple_goto(LocationGlobalRelative(lat, lon, int(ud)))
        while True:
            time.sleep(1)
            print("目前高度：", vehicle.location.global_relative_frame.alt)
            status()
            if float(ud)*1.02 >= float(vehicle.location.global_relative_frame.alt) >= float(ud)*0.98:
                break
        server.sql_update(ID, 'dronemode', '1')
        send('完成')
    else:
        send('差距過小、不移動')


def land(head):
    print("返回中")
    send('返回中')
    condition_yaw(head, False)
    while vehicle.heading != head:
        if head-5 <= vehicle.heading <= head+5:
            break
        else:
            time.sleep(1)
            print('延遲中')
    vehicle.mode = VehicleMode("LAND")
    while vehicle.armed:
        gps0 = "%s" % vehicle.gps_0
        print(gps0)
        server.sql_update(
            1, 'status', vehicle.location.global_relative_frame.alt)
        server.sql_update(1, 'dronebatt', vehicle.battery.voltage)
        server.sql_update(1, 'GPSInfo', str(gps0))
        gps = str(vehicle.location.global_relative_frame.lat) + \
            ',' + str(vehicle.location.global_relative_frame.lon)
        server.sql_update(1, 'lat_lon', gps)
        print('返回中')
        time.sleep(1)

    server.sql_update(ID, 'dronemode', '2')
    server.sql_update(ID, 'land', '')
    send('完成')
    vehicle.mode = VehicleMode("GUIDED")


def send(txt):
    server.sql_update(ID, 'massage', txt)


def condition_yaw(heading, relative):
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
        0,          # param 2, yaw speed (not used)
        direction,  # param 3, direction
                    isRelative,  # param 4, relative or absolute degrees
        0, 0, 0)    # param 5-7, not used
    # 发送指令
    vehicle.send_mavlink(msg)
    vehicle.flush()
    server.sql_update(ID, 'droneturn', '')
    send('完成')
    time.sleep(1)


def status():
    # 狀態輸出     高度 電量 gps
    gps0 = "%s" % vehicle.gps_0
    print(gps0)
    server.sql_update(1, 'status', vehicle.location.global_relative_frame.alt)
    server.sql_update(1, 'dronebatt', vehicle.battery.voltage)
    server.sql_update(1, 'GPSInfo', str(gps0))
    gps = str(vehicle.location.global_relative_frame.lat) + \
        ',' + str(vehicle.location.global_relative_frame.lon)
    print(gps)
    server.sql_update(1, 'lat_lon', gps)
    if float(vehicle.battery.voltage) < 21.3 and row[5] == 1:
        print('低電壓')
        send("低電壓、將強制降落")
        land(head)


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
        mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,
        0b0000101111000111,  # type_mask
        0, 0, 0,  # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z,  # m/s
        0, 0, 0,  # x, y, z acceleration
        0, 0)
    for x in range(0, abs(duration)):
        vehicle.send_mavlink(msg)
        time.sleep(0.3)

    server.sql_update(ID, 'forward_back', '')
    time.sleep(0.5)
    print('完成')
    send('完成')


def cam_control(cam):  # 置中'0'向右'1'向左'2'向上'3'向下'4'
    # control Mode:MODE_ANGLE_REF_FRAME
    # pitch angle: 正值向下，負值向上
    # yaw angle:   正值向右，負值向左
    # 雲台上下左右控制皆設定，以每秒50度旋轉18度
    # 旭展編輯撰寫
    global yaw, pitch
    if cam == '0':
        EH10.set_return_head_cmd()
        EH10.set_camera_zoomOut_cmd()     # camera zoom in
        pitch = 0
        yaw = 0
        time.sleep(5)
        EH10.set_camera_stop_zoom_cmd()

    if cam == '1':
        yaw = yaw+10
    if cam == '2':
        yaw = yaw-10
    if cam == '3':
        pitch = pitch-5
    if cam == '4':
        pitch = pitch+5
    if cam == '5':
        EH10.set_camera_zoomIn_cmd()     # camera zoom in
        time.sleep(0.66)
        EH10.set_camera_stop_zoom_cmd()  # camera stop zoom
    if cam == '6':
        EH10.set_camera_zoomOut_cmd()     # camera zoom in
        time.sleep(0.66)
        EH10.set_camera_stop_zoom_cmd()  # camera stop zoom

    EH10.set_movement_cmd(0, 5, 5, 0, 0, 50, pitch, 50, yaw)
    server.sql_update(ID, 'cam', '')

    print('完成')
    send('完成鏡頭操作')


def allmove(ms1, ma2, ma3):
    if ms1 != '0':
        send_body_ned_velocity(1, 0, 0, int(ms1))
    if ma2 != '0':
        send_body_ned_velocity(0, 1, 0, int(ma2))
    if ma3 != '0':
        condition_yaw(int(ma2), True)

    server.sql_update(ID, 'allmove_FW', '')
    server.sql_update(ID, 'allmove_LR', '')
    server.sql_update(ID, 'allmove_yaw', '')
    send("完成")


# ---------建立連線---------
server = sqlserver("test", '00000000')
row = server.sql_listen(1)

a = 0
while True:
    try:
        row = server.sql_listen(ID) 
        print(row)
        status()
        if not vehicle.armed:
            server.sql_update(ID, 'dronemode', 2)
        if row[1] != None:
            server.sql_update(ID, 'dronemode', 3)
            head, gpsnow = takeoff(row[1])
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
        if row[14] != None or row[15] != None or row[16] != None:
            allmove(row[14], row[15], row[16])
        if row[11] != None:
            cam_control(row[11])
        "EH10.set_movement_cmd(0, 5, 5, 0, 0, 50, pitch, 50, yaw)"
        time.sleep(1)
    except:
        time.sleep(1)
