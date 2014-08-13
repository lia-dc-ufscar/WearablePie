WearablePie
===========

This code is a PoC (Proof of Concept).
It has many design issues and the code has to be improved.

However, if you wish to join us on this adventure here are a few tips

Install archlinux:
http://archlinuxarm.org/platforms/armv6/raspberry-pi#qt-platform_tabs-ui-tabs2
http://raspberry-hosting.com/en/faq/cras-quis-nibh

Figure out IP address for raspberryPi
ssh root@ip-address (pass: root)

UPDATE PACKAGES
pacman -Sy

FIX DATE
timedatectl set-time "2014-08-07 10:00:45"

INSTALLING NECESSARY PACKAGES AND MODULES
pacman -S git
pacman -S vim
pacman -S python2
pacman -S python2-pip
pacman -S base-devel (10: gcc)
pacman -S gpsd
pacman -S netctl
pacman -S wpa_actiond
pacman -S zbar

pip2 install picamera
pip2 install rpi.gpio
pip2 install requests
pip2 install pyinotify

SETTING UP CAMERA
https://wiki.archlinux.org/index.php/Raspberry_Pi#Raspberry_Pi_camera_module
-  /boot/config.txt
	start_file = start_x.elf
	fixup_file = fixup_x.dat

	Increase gpu_mem from 64 to 128

	cma_lwm=
	cma_hwm=
	cma_offline_start=


GETTING CODE FROM GITHUB:
git clone https://github.com/lia-dc-ufscar/WearablePie.git


RUNNING INSTALL
./install

ENABLE AUTOCONNECTION FOR WIRELESS
systemctl enable netctl-auto@wlan0.service
