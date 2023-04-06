#!/bin/bash

sudo apt-get update

# 下載 python pip
sudo apt-get install python3
sudo apt-get install python3-pip -y

# 下載 python模組
sudo pip3 install pymavlink

sudo pip3 install dronekit 

# 安裝 pymysql 還需測試
sudo pip3 install Cython
sudo apt-get install python3-dev freetds-dev -y 
sudo pip3 install pymssql

python3 -m pip install pymysql



# 下載 git 及控制模組
sudo apt-get install git -y
git clone https://github.com/bruce1031/RCCS-raspberry.git -b master
cd RCCS-raspberry
git submodule update --init
cd install_package

# 安豬nginx

git clone  https://github.com/arut/nginx-rtmp-module
wget https://www.openssl.org/source/openssl-1.1.1.tar.gz 
sudo  tar -xvf nginx-1.18.0.tar.gz -C /usr/local
mv nginx-rtmp-module/ /usr/local/nginx-1.18.0/
sudo  tar -xvf openssl-1.1.1.tar.gz -C /usr/local/nginx-1.18.0/
cd /usr/local/nginx-1.18.0/
sudo ./configure --prefix=/usr/local/nginx --add-module=nginx-rtmp-module --with-http_ssl_module --with-debug --with-openssl=openssl-1.1.1
sudo make
sudo make install



# 更改uart端口
sudo raspi-config nonint do_serial 0
sudo sh -c 'echo "enable_uart=1" >> /boot/config.txt'
echo -e "dtoverlay=pi3-miniuart-bt\ndtoverlay=pi3-disable-bt" | sudo tee -a /boot/config.txt 

# 開機自動啟動


# 開啟所有權限
#
