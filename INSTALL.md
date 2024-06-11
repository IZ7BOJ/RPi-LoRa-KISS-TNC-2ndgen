# Installation and running the RPi-LoRa-Gateway

Note: the instructions consider aprx as APRS software, configured as internet rx-gateway. If you chose different aprs software, don't consider the aprx instructions

## Install needed base packages
```
sudo apt install git aprx pip3 python3 python3-rpi.gpio python3-spidev python3-pil python3-smbus
```

## Checkout the Kiss TNC code
Enter following commands:<br/>
```
cd /home/pi/Applications/ (this is only example, you can chose directory that you prefer)
sudo git clone https://github.com/IZ7BOJ/RPi-LoRa-KISS-TNC-2ndgen.git
```

## Install the SX126x python driver (if sx126x is used)
Enter following commands:<br/>
```
pip3 install LoRaRF
```
The complete installation instructions for the driver can be found here: https://github.com/chandrawi/LoRaRF-Python

## Install the SX127x python driver (if sx127x is used)
Enter following commands:<br/>
```
cd RPi-LoRa-KISS-TNC-2ndgen
git clone https://github.com/mayeranalytics/pySX127x.git
```
Overwrite original /pySX127x/SX127x/board_config.py with board_config.py of my github:
```
sudo mv board_config.py ./pySX127x/SX127x/board_config.py

```
Overwrite original /pySX127x/SX127x/LoRa.py with LoRa.py of my github:
```
sudo mv LoRa.py ./pySX127x/SX127x/LoRa.py

```

The original files are written for Modtronix Lora Module, which uses more GPIO lines than we need.
In order to save resources of our raspberry, I deleted unused lines from board_config.py.
Note that KISS TNC won't work if you don't overwrite board_config.py!!


## Install Display driver (is display is used)
```
sudo pip3 install adafruit-circuitpython-ssd1306
```
Note: I2C bus musst be enabled on your raspberry! Follow these steps:
```
sudo raspi-config
```
Then "Interfacing Options"->"I2C", confirm "yes" at the end.
For troubleshooting on the display, you can install "i2c-tools" and try to detect the display with "i2cdetect -y 1"

## Enable SPI bus on raspberry
```
sudo raspi-config
```
Then "Interfacing Options"->"SPI", confirm "yes" at the end.

## RPi-KISS-TNC Configuration
All the main parameters are enclosed in the file config.py .<br/>
The comments in the file will help you to understand every parameter.<br/>
If the log file is enabled, be sure to give the right permissions to the log file, otherwise the software will not start.<br/>
Select the correct version of Lora chip (sx126x/127x)
Enable display only if is connected, otherwise you'll get blocking error.

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
## Support
For questions, write me at iz7boj [at] gmail.com
