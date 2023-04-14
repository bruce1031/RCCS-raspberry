#!/bin/bash
# 尚未加入進度條
# 尚未加入錯誤問題輸出
# 尚未加入完成時提示
# 尚未加入如已完成安裝，略過

sudo apt-get update

#安裝額外模組
sudo apt-get install libssl-dev -y
sudo apt-get install libsdl-dev -y
sudo apt-get install libavcodec-dev -y
sudo apt-get install libavutil-dev -y
sudo apt-get install libkrb5-dev libssl-dev libffi-dev -y


# 下載 python pip
sudo apt-get install python3
sudo apt-get install python3-pip -y
sudo pip install -U pip

# 下載 python模組
sudo pip3 install pymavlink
sudo pip3 install dronekit 
sudo pip3 install pyserial

# 安裝 pymysql 還需測試
sudo pip3 install Cython
sudo apt-get install python3-dev freetds-dev -y 
sudo pip3 install pymssql


# 下載 git 及控制模組，並修改權限
#sudo apt-get install git -y
#git clone https://github.com/bruce1031/RCCS-raspberry.git -b master
#cd RCCS-raspberry
#git submodule update --init

#手動創建autostart.sh檔案
echo 'sudo python /home/pi/RCCS-raspberry/start.py &' > /home/pi/autostart.sh
sudo chmod 777 autostart.sh

# 安豬nginx及影像串流ffmpeg
cd install_package
git clone  https://github.com/arut/nginx-rtmp-module
wget https://www.openssl.org/source/openssl-1.1.1.tar.gz 
sudo  tar -xvf nginx-1.18.0.tar -C /usr/local
sudo mv nginx-rtmp-module/ /usr/local/nginx-1.18.0/
sudo  tar -xvf openssl-1.1.1.tar.gz -C /usr/local/nginx-1.18.0/
cd /usr/local/nginx-1.18.0/
sudo ./configure --prefix=/usr/local/nginx --add-module=nginx-rtmp-module --with-http_ssl_module --with-debug --with-openssl=openssl-1.1.1
sudo make
sudo make install
sudo apt-get install ffmpeg -y

# 修改nginx文件
echo -e "#RTMP 服务
rtmp 
{
	server
	{
        #指定服务端口
	    listen 1935;
	    chunk_size 4096;

        #指定RTMP流应用
        application live
        {
            live on;
        }
    }
}
" | sudo tee -a /usr/local/nginx/conf/nginx.conf
#啟動nginx
sudo /usr/local/nginx/sbin/nginx

# 更改uart端口
sudo raspi-config nonint do_serial 0
sudo sh -c 'echo "enable_uart=1" >> /boot/config.txt'
echo -e "dtoverlay=pi3-miniuart-bt\ndtoverlay=pi3-disable-bt" | sudo tee -a /boot/config.txt 
sudo raspi-config nonint do_serial 1

# 開機自動啟動

sudo sed -i '/^exit 0/i \  /home\/pi\/autostart.sh \&\n' /etc/rc.local

# 開啟所有權限

# 安裝zeritire
curl https://raw.githubusercontent.com/zerotier/ZeroTierOne/master/doc/contact%40zerotier.com.gpg | gpg --dearmor | sudo tee /usr/share/keyrings/zerotierone-archive-keyring.gpg >/dev/null
RELEASE=$(lsb_release -cs)
echo "deb [signed-by=/usr/share/keyrings/zerotierone-archive-keyring.gpg] http://download.zerotier.com/debian/$RELEASE $RELEASE main" | sudo tee /etc/apt/sources.list.d/zerotier.list
sudo apt update
sudo apt install -y zerotier-one
sudo zerotier-cli join 632ea290851611e0

#加入d-link網路
allow-hotplug wwan0
iface wwan0 inet dhcp
echo -e "allow-hotplug wwan0\iface wwan0 inet dhcp" | sudo tee -a /etc/network/interfaces

# 輸出目前無人機編號，網路ip

# 重新啟動
sudo reboot
