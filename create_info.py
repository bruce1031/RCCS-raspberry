import json
import subprocess
from Scripts.sql_server.SQLS import sqlserver
from cryptography.fernet import Fernet
#是否要加入json檔案可使用時間

#將資料轉換成json並加密
while True:
    try:
        con = str(input("請聯絡管理員打開zerotier權限，完成請打入（y）:"))
        if con == 'y':
            # 執行指令，取得Zerotier IP
            output = subprocess.check_output(["sudo", "zerotier-cli", "listnetworks"]).decode("utf-8")
            lines = output.strip().split('\n')
            lines=lines[1].split()
            zerotier_ip = ""

            # 搜尋Zerotier IP
            for line in lines:
                if "200" in line:
                    parts = lines
                    if len(parts) > 2:
                        print(parts[8])
                        zerotier_ip = parts[8].split('/')[0]
                        break
            break
        else:
            continue
    except:
        print('權限尚未開啟，請檢察網路，或是聯絡管理員')



#儲存sql帳號密碼
account = "test"
password = "00000000"


#drone ID
sql_data = sqlserver("test", '00000000')
id=sql_data.create_new_drone_id_database()

#上傳ip到伺服器
sql_data.sql_update(id, 'ip', zerotier_ip)


#加密
data = {
    'sql_account': account,
    'sql_password': password,
    'drone_id' : id,
    'zerotier_ip_address' :zerotier_ip
}

# 將 JSON 轉換成字串
json_data = json.dumps(data).encode()

# 生成金鑰
key = Fernet.generate_key()

# 初始化Fernet對象
fernet = Fernet(key)
# 加密資料
encrypted_data = fernet.encrypt(json_data)

# 使用金鑰解密資料
decrypted_data = fernet.decrypt(encrypted_data)

# 將解密後的字串轉換回 JSON 資料
decrypted_json_data = json.loads(decrypted_data.decode())


# 驗證解密後的資料是否與原始資料相同

if decrypted_json_data == data:
    # 將IP存入JSON檔案中(加密)
    with open('info.json', 'wb') as f:
        f.write(encrypted_data)
    print('已加密')
    with open('encrypted.txt', 'wb') as f:
        f.write(key)
else:
    # 將IP存入JSON檔案中（未加密）
    with open('info.json', 'w') as f:
        json.dump(data, f)
    print('無加密')
