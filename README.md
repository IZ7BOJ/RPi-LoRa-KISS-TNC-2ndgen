![RPi-LoRa-KISS-TNC-2ndgen](/doc/images/LoRa_RPi_Companion_2.jpeg)
# Raspberry Pi LoRa KISS TNC

This software emulates a KISS TNC and controls a hardware LoRa transceiver of 1st and 2nd generation (SX127x/SX126x)
connected to the Raspberry´s SPI. That makes it possible to use existing APRS
software, like aprx or direwolf, with LoRa radio communication, in order to build a powerful APRS digipeater with possibility
to mix legacy FSK 1200bps with new Lora technology.

The software shall be executed together with the APRS digi [APRX](https://github.com/PhirePhly/aprx), which connects via "KISS over TCP" and provides
powerful APRS digipeating and I-gate functionality for LoRa-APRS.

The Software keeps the compatibility with both standard AX25 packets and Austrian team packet style (called "OE_style").

## Hardware compatibility

The LoRa KISS TNC runs on Raspberry Pi 2 or newer together with the SX126x/SX127x LoRa Modules.
128x64 I2C Display (based os SSD1306chipset) is supported for showing last rx/tx packets. Can be enabled/disabled inside config.py

Theoretically, all LoRa modules using SX127x (RFM9x) or SX126x series (SX1261, SX1262, SX1268) or LLCC68 will compatible. However, I personally tested the following configuration:
* Raspberry Pi3
* Ebyte E22-400M30S Lora Module
* RFM96 Lora Module

Most useful and used parameters can be changed inside config.py. Specific section for sx127x/sx126x are present.

A Hat PCB has been developed by Michele I8FUC, however LoRa modules can be wired up to the Raspberry Pi directly aswell. 
See the [schematic](doc/LoRa_RPi_Companion_2022.pdf) and the images [images](doc/images) for further details.
Note that the GPIO assignment in config.py refers to this schematic. Change it in case of custom assignment.

### Wiring Connections
Power pins, SPI pins, `RESET`, IRQ pins must be connected between RPi and LoRa module in both sx126x/127x cases.
The default SPI port is using bus id 0 and cs id 0. 
DIO1 must be connected for both sx127x/sx126x because is used as RX IRQ.
BUSY, TXEN and RXEN must be connected in case of SX126x Ebyte module because are used to manage the RX/TX switch of the module

Note: The  GPIO pins are declared with Broadcom pin numbering, they does not indicate the position on the physical connector! To see the correspondance between them, see: https://pinout.xyz/ 

## Installation
Read INSTALL.md for complete Software and Lora/display libraries installation guide

### To Do
* Get buttons working

### Credits
This software is an evolution of KISS TNC made by TOM OE9HTK for Lora 1st generation module:
https://github.com/tomelec/RPi-LoRa-KISS-TNC
Thanks TOM for nice work and starting idea

The PCB is designed by Michele I8FUC.
Thanks Michele for nice design and support during Software testing.
