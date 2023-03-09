import pymssql
import time


class sqlserver:
    def __init__(self, user, password):
        "self.host = '172.23.70.50'"
        self.host = '192.168.0.69'  # 網内使用
        self.server = 'georobot\GEOSAT'
        self.port = '49172'
        self.user = user
        self.password = password
        self.error_count = 0

        while True:
            try:
                self.conn = pymssql.connect(host=self.host, server=self.server, port=self.port,
                                            user=self.user, password=self.password)
                self.conn.autocommit(True)
                self.cursor = self.conn.cursor(as_dict=True)  # 建立物件

            except Exception as e:
                print("sql connect error!")
                print(e)
                print("keep trying to reconnect...")
                self.error_count += 1
                if self.error_count == 5:
                    print("sql connect failed!")
                    time.sleep(1)
                    break

            else:
                print("connecting!")
                break

    def connect(self):
        while True:
            try:
                self.conn = pymssql.connect(host=self.host, server=self.server, port=self.port,
                                            user=self.user, password=self.password)
                self.conn.autocommit(True)
                self.cursor = self.conn.cursor()  # 建立連線
            except Exception as e:
                print("sql connect error!")
                print(e)
                print("keep trying to reconnect...")
                self.error_count += 1
                if self.error_count == 5:
                    print("sql connect failed!")
                    break
            else:
                print("connecting!")
                break

    def sql_listen(self, ID):
        '''查詢所有資料(ID , 欄位）'''
        self.cursor = self.conn.cursor()
        try:
            self.cursor.execute(
                f"SELECT * FROM [UAV].[dbo].[UAV_test] WHERE id={ID}")  # 輸入sql語法
        except:
            self.cursor.execute(
                f"SELECT * FROM [UAV].[dbo].[UAV_test] WHERE id='{ID}'")
        row = self.cursor.fetchone()

        return row

    def sql_select(self, ID, event):
        '''查詢資料(ID , 欄位）'''
        self.cursor = self.conn.cursor()
        try:
            self.cursor.execute(
                f"use uav SELECT {event} from UAV_test WHERE id='{ID}'")
        except:
            self.cursor.execute(
                f"use uav SELECT '{event}' from UAV_test WHERE id='{ID}'")
        row = self.cursor.fetchone()
        row = row[0]

        return row

    def sql_update(self, ID, event, data):
        '''
        輸入(ID , 欄位名稱 , 更新資料)
        '''
        self.cursor = self.conn.cursor()
        if data == '' or data == None:
            data = "null"
        else:
            data = str(data)

        try:
            self.cursor.execute(
                f"USE UAV UPDATE UAV_test SET {event}={data} WHERE id={ID}")
        except:
            self.cursor.execute(
                f"USE UAV UPDATE UAV_test SET {event}='{data}' WHERE id='{ID}'")


if __name__ == '__main__':
    d = 0
    D = 0
    col_Table = ['id', 'takeoff', 'land', 'massage', 'status', 'dronemode', 'up_down', 'lat_lon', 'droneturn',
                 'forward_back', 'allmove', 'cam', 'dronebatt', 'GPSInfo', 'allmove_FW', 'allmove_LR', 'allmove_yaw', 'connect_status']
    #sql_data = sqlserver("test", '00000000')
    #print(sql_data.sql_select(1, 'takeoff'))
    while True:

        event = str(input('updata(ud)/read(r)'))

        if event == 'ud':
            print('欄位名稱: 1-id , 2-takeoff , 3-land , 4-massage , 5-status , 6-dronemode , 7-up_down , 8-lat_lon , 9-droneturn , 10-forward_back , 11-allmove , 12-cam , 13-dronebatt , 14-GPSInfo',
                  '15-allmove_FW', '16-allmove_LR', '17-allmove_yaw', '18-connect_status')
            a = input('輸入欄位名稱or編號:')
            try:
                a = int(a)
                if a >= 0 and a <= len(col_Table):
                    a = col_Table[a-1]
            except:
                a = str(a)
            b = input("輸入更改資料:")

            sql_data = sqlserver("test", '00000000')
            try:
                original_data = sql_data.sql_listen(1)
                sql_data.sql_update(1, a, b)
                revise_data = sql_data.sql_listen(1)
                ok = False
                for i in range(len(revise_data)):
                    if original_data[i] != revise_data[i]:
                        print(
                            f"更動欄位:\033[1;36m {a}\033[0m\n更動資料:\033[1;36m {original_data[i]} --> {revise_data[i]}\033[0m")
                        print("更改完成後資料顯示:",   revise_data)
                        ok = True
                        break
                if ok == False:
                    print('無資料更新,資料庫:', sql_data.sql_listen(1))
                break

            except:
                print("錯誤，請重新輸入")
                d = d+1
                if d == 3:
                    print('錯誤多次，離開程式')
                    break
        if event == 'r':
            sql_data = sqlserver("test", '00000000')
            print("目前資料庫:", sql_data.sql_listen(1))
            break

        else:
            print("錯誤，請重新輸入")
            D = D+1
            if D == 3:
                print('錯誤多次，離開程式')
                break
