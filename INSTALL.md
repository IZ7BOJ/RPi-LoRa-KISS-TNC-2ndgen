# Installation and running the RPi-LoRa-Gateway

Note: the instructions consider aprx as APRS software, configured as internet rx-gateway. If you chose different aprs software, don't consider the aprx instructions

## Install needed packages
```
sudo apt install git aprx pip3 python3 python3-rpi.gpio python3-spidev python3-pil python3-smbus
```

## Checkout the Kiss TNC code
Enter following commands:<br/>
```
cd /home/pi/Applications/ (this is only example, you can chose directory that you prefer)
git clone https://github.com/tomelec/RPi-LoRa-KISS-TNC.git
```

## Install the SX126x python driver
Enter following commands:<br/>
```
pip3 install LoRaRF
```
The complete installation instructions for the driver can be found here: https://github.com/chandrawi/LoRaRF-Python

## RPi-KISS-TNC Configuration
All the main parameters are enclosed in the file config.py .<br/>
The comments in the file will help you to understand every parameter.<br/>
If the log file is enabled, be sure to give the right permissions to the log file, otherwise the software will not start.<br/>


## Aprx Configuration
Afterwards configure as following:
### Edit aprx/aprx.conf.lora-aprs file
Type:
```
cd
cd RPi-LoRa-KISS-TNC
sudo cp aprx/aprx.conf.lora-aprs /etc/aprx.conf
pico -w /etc/aprx.conf
```
to copy and then open the config file.

The most important settings are:
* **mycall**<br/>
Your call with an apropriate SSID suffix<br/>[Paper on SSID's from aprs.org](http://www.aprs.org/aprs11/SSIDs.txt) 
* **myloc**<br/>
NMEA lat/lon form:
```
lat ddmm.mmN lon dddmm.mmE
```
Example:
```
lat 4812.52N lon 01622.39E
```
(simplest way to find the right coordinats for this? Go to [aprs.fi](http://www.aprs.fi) on your location right-click and choose "Add marker" then click on the marker and you should see your coordinates in the NMEA style - enter this infos without any symbols into the config file as seen in the example above)

* **passcode**<br/>
see [see here to generate appropiate setting](https://apps.magicbug.co.uk/passcode/)
* **server**<br/>
either leave the default server or chose from http://status.aprs2.net/

to save and close the file do:
`Strg + x` -> Y -> Enter

## Enable SPI port on raspberry
In order to connect to a LoRa module, SPI port must be enabled. 
For Raspberry pi OS, this is done by set SPI interface enable using raspi-config or edit /boot/config.txt by adding following line:
```
dtparam=spi=on
```

## give execution permission to Start file
```
sudo chmod +x Start_lora-tnc.py
```

## Start the LoRa KISS TNC and aprx server instance
```
sudo Start_lora-tnc.py
sudo aprx
```

The Software will print useful informations on the screen. If you want to run Kiss TNC as daemon, use:
```
sudo Start_lora-tnc.py>/dev/null &
```

## Stop the server's
```
sudo killall aprx Start_lora-tnc.py
```
