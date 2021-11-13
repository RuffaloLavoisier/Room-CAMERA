echo start $(date +%T)
echo "package update and upgrade"
sudo apt-get update && sudo apt-get upgrade -y
echo "library download"
sudo apt-get install libjpeg-dev libpng-dev libtiff-dev libgtk-3-dev libavcodec-extra libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libjasper1 libjasper-dev libatlas-base-dev gfortran libeigen3-dev libtbb-dev -y
echo "check pip and pip3"
sudo apt-get install python-pip -y
sudo apt-get install python3-pip -y

echo "install numpy"
sudo pip3 install numpy #python3.x
sudo pip install numpy #python2.x
echo "install git"
sudo apt-get install git -y
#git clone https://github.com/dlime/Faster_OpenCV_4_Raspberry_Pi.git
cd /home/pi/Software-v2/install_opencv/debs
sudo dpkg -i OpenCV*.deb
sudo ldconfig
echo "install requirement package"
cd /home/pi/Software-v2/
sudo pip3 install -r requirements.txt
echo done $(date +%T)
