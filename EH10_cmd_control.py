'''
Serial Control Connection: TTL 3.3v UART baud: 115200, 8/1/N, HEX

EH10 control gimbal Movement:
CMD_CONTROL Frame(20 Bytes, HEX): FF 01 0F 10 RM PM YM Rsl Rsh Ral Rah Psl Psh Pal Pah Ysl Ysh Yal Yah CS
*HEAD: FF010F10
*RM, PM, YM: Roll, pitch, yaw control mode
*ROLL SPEED:  Rs = 0xRshRsl, ROLL ANGLE:  Ra = 0xRahRal
*PITCH SPEED: Ps = 0xPshPsl, PITCH ANGLE: Pa = 0xPahPal
*YAW SPEED:   Ys = 0xYshYsl, YAW ANGLE:   Ya = 0xYahYal
*CS: checksum, RM + ... + Yah, get LOW Byte

## control mode: 00(HEX) = MODE_NO_CONTRL, 01 = MODE_SPEED, 02 = MODE_ANGLE, 03 = MODE_SPEED_ANGLE,
##               04 = MODE_RC, 05 = MODE_ANGLE_REF_FRAME(±360° range), 06 = MODE_RC_HIGH_RES
## speed: 2 byte signed, little-endian order, units: 0.1220740379 deg/sec
## angle: 2 byte signed, little-endian order, units: 0.02197265625 degree, range -32768 ~ 32767
## sl = Speed Low byte, sh = speed high byte, al = angle low byte, ah = angle high byte.
## CS = body checksum, checksum is calculated as a sum of bytes from 'RM'to 'Yah'.
##      if calculated checksum over 1 Byte, just take 1 Byte(LOW Byte),
##      e.g. CS calculated sum is 0x209, then CS should be 0x09.
## *If use RC mode, PA/YA is RC value should be -500~500, (-500 is PWM 1000ms, 0 is PWM 1500ms, 500 is PWM 2000ms)*
'''
from decimal import Decimal, ROUND_HALF_UP
import serial
import time

class Gimbal:
    def __init__(self, port, baud):
        self.port = port
        self.baudrate = baud
        self.serial_port = None
        self.error_count = 0
        #print(f"set serial port:{self.port} baud rate:{self.baudrate}")

        while True:
            try:
                self.serial_port = serial.Serial(self.port, self.baudrate)
            except Exception as e:
                print("serial connect error!")
                print(e)
                print("keep trying to reconnect...")
                self.error_count += 1
                if self.error_count == 5:
                    print("seril port initialize failed!")
                    break
            else:
                print("connecting!")
                break
            time.sleep(2)

    def serial_connect(self):
        self.error_count = 0
        while True:
            try:
                self.serial_port = serial.Serial(self.port, self.baudrate)
            except Exception as e:
                print("serial connect error!")
                print(e)
                print("keep trying to reconnect...")
                self.error_count += 1
                if self.error_count == 5:
                    print("seril port initialize failed!")
                    break
            else:
                print("connecting!")
                break
            time.sleep(2)

    def send_cmd(self,cmd):
        if self.serial_port is None:
            self.serial_connect()
        elif self.serial_port is not None:
            success_bytes = self.serial_port.write(serial.to_bytes(cmd))
            return success_bytes
            
    ## rm = roll_controll_mode, pm = pitch_controll_mode, ym = yaw_controll_mode,
    ## rs = roll_speed, ra = roll_angle, ps = pitch_speed, pa = pitch_angle, ys = yaw_speed, ya = yaw_angle)
    ## control mode: 0 = MODE_NO_CONTRL, 1 = MODE_SPEED, 2 = MODE_ANGLE, 3 = MODE_SPEED_ANGLE,
    ##               4 = MODE_RC, 5 = MODE_ANGLE_REF_FRAME(±360° range), 6 = MODE_RC_HIGH_RES
    ## speed(deg/sec) and angle(degree) could be positive or negative
    ## if use MODE_RC, pa and ya range is int 1000~2000 (pwm)
    ## Use MODE_ANGLE_REF_FRAME can go to the specified angle.
    def set_movement_cmd(self, rm, pm, ym, rs, ra, ps, pa, ys, ya):
        time.sleep(1)
        ## CMD_CONTROL Frame
        CMD_CONTROL = []

        ## speed , angle Unit
        speed_unit = 0.1220740379
        angle_unit = 0.02197265625

        ## input Frame HEAD
        CMD_CONTROL = [0xFF, 0x01, 0x0F, 0x10]

        ## control mode
        CMD_CONTROL.append(rm)
        CMD_CONTROL.append(pm)
        CMD_CONTROL.append(ym)
    
        ## speed and angle
        if pm == 4:
            pa = pa - 1500
        else:
            pa = int(Decimal(str(pa/angle_unit)).quantize(Decimal("0"), ROUND_HALF_UP))
        if ym == 4:
            ya = ya - 1500
        else:
            ya = int(Decimal(str(ya/angle_unit)).quantize(Decimal("0"), ROUND_HALF_UP))

        rs = int(Decimal(str(rs/speed_unit)).quantize(Decimal("0"), ROUND_HALF_UP))  # Rounding Decimals to The Nearest Whole Number
        ra = int(Decimal(str(ra/angle_unit)).quantize(Decimal("0"), ROUND_HALF_UP))
        ps = int(Decimal(str(ps/speed_unit)).quantize(Decimal("0"), ROUND_HALF_UP))
        ys = int(Decimal(str(ys/speed_unit)).quantize(Decimal("0"), ROUND_HALF_UP))
    
        ## Two Bytes are split into HIGH Byte and LOW Byte
        rpy_speed_angle = [rs, ra, ps, pa, ys, ya]
        for i in rpy_speed_angle:
            CMD_CONTROL.append(i & 0xFF)
            CMD_CONTROL.append((i >> 8) & 0xFF)

        ## checksum
        checksum = 0
        for i in CMD_CONTROL[4:]:
            checksum += i
        CMD_CONTROL.append(checksum & 0xFF)  # take only one byte for CMD_CONTROL frame's checksum

        self.send_cmd(CMD_CONTROL)
        return CMD_CONTROL

    ## Return head
    def set_return_head_cmd(self):
        CMD_CONTROL = [0x3E, 0x45, 0x01, 0x46, 0x12, 0x12]
        self.send_cmd(CMD_CONTROL)
        return CMD_CONTROL
    
    ## Look down
    def set_look_down_cmd(self):
        CMD_CONTROL = [0x3E, 0x45, 0x01, 0x46, 0x11, 0x11]
        self.send_cmd(CMD_CONTROL)
        return CMD_CONTROL

    ## Center yaw
    def set_center_yaw_cmd(self):
        CMD_CONTROL = [0x3E, 0x45, 0x01, 0x46, 0x23, 0x23]
        self.send_cmd(CMD_CONTROL)
        return CMD_CONTROL

    ## Open gimbal's attitude continuous feedback
    def set_open_auto_feedback_cmd(self):
        CMD_CONTROL = [0x3E, 0x3E, 0x00, 0x3E, 0x00]
        self.send_cmd(CMD_CONTROL)
        return CMD_CONTROL

    ## auto feedback interval time: unit:ms
    def set_auto_feedback_interval_time_cmd(self, interval_time_ms):
        ## Frame header: 3E 55 15 6A, 0x58 no idea what it mean
        CMD_CONTROL = [0x3E, 0x55, 0x15, 0x6A, 0x58]

        ## interval time
        CMD_CONTROL.append(interval_time_ms & 0xFF)
        CMD_CONTROL.append((interval_time_ms >> 8) & 0xFF)

        CMD_CONTROL.append(0x0D)  # 0x0D no idea what it mean
        for i in range(17):
            CMD_CONTROL.append(0x00)
        
        ## checksum
        checksum = 0
        for i in CMD_CONTROL[4:8]:
            checksum += i
        CMD_CONTROL.append(checksum & 0xFF)  # & 0xff , take only one byte for CMD_CONTROL frame's checksum

        self.send_cmd(CMD_CONTROL)
        return CMD_CONTROL

    ## Close gimbal's attitude continuous feedback
    def set_close_auto_feedback_cmd(self):
        CMD_CONTROL = [0x3E, 0x3D, 0x00, 0x3D, 0x00]
        self.send_cmd(CMD_CONTROL)
        return CMD_CONTROL

    ###################################################################################################################
    ## Camera_control_cmd: different model use different commands, so please use command according to your actual model
    ## camera model Z10F, Z18F, Z30F, "Q10F", Q18F, Q30F command, we use Q10F

    ## camera zoom out
    def set_camera_zoomOut_cmd(self):
        CAMERA_CMD_CONTROL = [0x81, 0x01, 0x04, 0x07, 0x37, 0xFF]
        self.send_cmd(CAMERA_CMD_CONTROL)
        return CAMERA_CMD_CONTROL

    ## camera zoom in
    def set_camera_zoomIn_cmd(self):
        CAMERA_CMD_CONTROL = [0x81, 0x01, 0x04, 0x07, 0x27, 0xFF]
        self.send_cmd(CAMERA_CMD_CONTROL)
        return CAMERA_CMD_CONTROL

    ## camera stop zoom
    def set_camera_stop_zoom_cmd(self):
        CAMERA_CMD_CONTROL = [0x81, 0x01, 0x04, 0x07, 0x00, 0xFF]
        self.send_cmd(CAMERA_CMD_CONTROL)
        return CAMERA_CMD_CONTROL

    ## photograph /record action command: 81 01 04 68 xx FF
    ## xx = :
    ## 01 photograph
    ## 02 start record
    ## 03 stop record
    ## 04 invert record state
    ## 05 switch to record mode or picture mode
    def set_camera_photograph_cmd(self):
        CAMERA_CMD_CONTROL = [0x81, 0x01, 0x04, 0x68, 0x01, 0xFF]
        self.send_cmd(CAMERA_CMD_CONTROL)
        return CAMERA_CMD_CONTROL
    def set_camera_start_record_cmd(self):
        CAMERA_CMD_CONTROL = [0x81, 0x01, 0x04, 0x68, 0x02, 0xFF]
        self.send_cmd(CAMERA_CMD_CONTROL)
        return CAMERA_CMD_CONTROL
    def set_camera_stop_record_cmd(self):
        CAMERA_CMD_CONTROL = [0x81, 0x01, 0x04, 0x68, 0x03, 0xFF]
        self.send_cmd(CAMERA_CMD_CONTROL)
        return CAMERA_CMD_CONTROL
    def set_camera_switch_mode_cmd(self):
        CAMERA_CMD_CONTROL = [0x81, 0x01, 0x04, 0x68, 0x05, 0xFF]
        self.send_cmd(CAMERA_CMD_CONTROL)
        return CAMERA_CMD_CONTROL

    ## Inquiry record/photograph state
    ## Camera Feedback:
    ## 81 09 04 68 00 FF stop record
    ## 81 09 04 68 01 FF recording
    ## 81 09 04 68 10 FF photograph mode
    def set_camera_get_state_cmd(self):
        CAMERA_CMD_CONTROL = [0x81, 0x09, 0x04, 0x68, 0xFF]
        self.send_cmd(CAMERA_CMD_CONTROL)
        return CAMERA_CMD_CONTROL


if __name__ == '__main__':
    EH10 = Gimbal("/dev/ttyACM0", 115200)
    ## example1: ROLL no control, PITCH speed mode 1.22degree/sec, YAW speed mode 1.22degree/sec.
    CMD_CONTROL_FRAME = EH10.set_movement_cmd(0, 1, 1, 0, 0, 1.22, 0, 1.22, 0)

    ## Example2: ROLL no control, PITCH angle mode to 40 degree down REF home position,
    ## YAW angle mode 40 degree left REF home position.
    #CMD_CONTROL_FRAME = EH10.set_movement_cmd(0, 5, 5, 0, 0, 0, 40, 0, -40)

    ## Example3: RC control pitch down( PWM = 1920, PA value = 1920-1500 = 420),
    ## RC control Yaw left (PWM = 1050, YA value = 1050-1500 = -450)
    #CMD_CONTROL_FRAME = EH10.set_movement_cmd(0, 4, 4, 0, 0, 0, 1920, 0, 1050)

    ## Open gimbal's attitude continuous feedback
    #CMD_CONTROL_FRAME = EH10.set_open_auto_feedback_cmd()

    ## set auto feedback interval time: unit:ms
    #CMD_CONTROL_FRAME = EH10.set_auto_feedback_interval_time_cmd(1000)

    print(" ".join(format(x, '02x') for x in CMD_CONTROL_FRAME))
    #rpi_ser.write(serial.to_bytes(CMD_CONTROL_FRAME))  # serial transmit data to EH10(control command)