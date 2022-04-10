![RPi-LoRa-KISS-TNC-2ndgen](/doc/images/LoRa_RPi_Companion_2.jpeg)
# Raspberry Pi LoRa KISS TNC

This project emulates a KISS TNC and controls a hardware LoRa transceiver 2nd generation (SX126x)
connected to the Raspberry´s SPI. That makes it possible to use existing APRS
software, like aprx or direwolf, with LoRa radio communication, in order to build a powerful APRS digipeater with possibility
to mix legacy FSK 1200bps with new Lora technology.

The current application is to run the KISS TNC together with the APRS digi [APRX](https://github.com/PhirePhly/aprx), which connects via "KISS over TCP" and provides
powerful APRS digipeating and I-gate functionality for LoRa-APRS.

The Software keeps the compatibility with both standard AX25 packets and Austrian team packet style (called "OE_style").

## Hardware compatibility

The LoRa KISS TNC runs on Raspberry Pi 2 or newer together with the SX126x LoRa Module.

Theoretically all LoRa modules using SX126x series (SX1261, SX1262, SX1268) or LLCC68 will compatible. However, I personally tested the following configuration:
* Raspberry Pi3
* Ebyte E22-400M30S Lora Module

A Hat PCB has been developed by Michele I8FUC, however LoRa modules can be wired up to the Raspberry Pi directly aswell. 
See the [schematic](doc/LoRa_RPi_Companion_2022.pdf) and the images [images](doc/images) for further details.
Note that the GPIO mapping of the PCB is different from the one reported below! GPIO must be reassigned.

### Wiring Connections

Power pins, SPI pins, `RESET`, `BUSY`, IRQ, TXEN, RXEN pins must be connected between RPi and LoRa module.
The default SPI port is using bus id 0 and cs id 0. 
DIO1 must be connected because is used as RX IRQ. 
TXEN and RXEN must be connected because are used to manage the RX/TX switch of the module
The pins declared in the default config.py are as follows, but can be modified as you prefer

Note: The  GPIO pins are declared with Broadcom pin numbering, they does not indicate the position on the physical connector! To see the correspondance between them, see: https://pinout.xyz/ 

| Semtech SX126x | Raspberry Pi |
| :------------: | :------:|
| VCC | 3.3V |
| GND | GND |
| SCK | GPIO 11 |
| MISO | GPIO 9 |
| MOSI | GPIO 10 |
| NSS | GPIO 8 |
| RESET | GPIO 22 |
| BUSY | GPIO 23|
| DIO1 | GPIO 26 |
| TXEN | GPIO 5 |
| RXEN | GPIO 25 |

## Installation

Read INSTALL.md for complete Software installation guide

## Development

This program and documentation is in a very early state and very experimental.
Only the LoRa radio modem of the gateway board is supported at the moment.
Display and buttons are not working.

### To Do
* Get display and buttons working

### Credits
This software is an evolution of KISS TNC made by TOM OE9HTK for Lora 1st generation module:
https://github.com/tomelec/RPi-LoRa-KISS-TNC

Thanks TOM for nice work and starting idea
