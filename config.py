## Config file for RPi-LoRa-KISS-TNC 2nd generation

## Lora Module selection
sx127x = True #if True, enables sx127x family, else sx126x

## Display enable and font
disp_en = False
font_size = 8

## Log enable and path
log_enable = True
logpath='/var/log/lora/lora.log' #log filename. Give r/w permission!

## KISS Settings
# Where to listen?
# TCP_HOST can be "localhost", "0.0.0.0" or a specific interface address
# TCP_PORT as configured in aprx.conf <interface> section
TCP_HOST = "0.0.0.0"
TCP_PORT = 10001

## Hardware Settings
# See datasheets for detailed pinout.
# The default pin assignment refers to PCB designed by I8FUC.
# The user can wire the module by his own and change pin assignment.
# assign "-1" if the pin is not used

# Settings valid for both SX126x and SX127x
busId = 0 #SPI Bus ID. Must be enabled on raspberry (sudo raspi-config). Default is 0
csId = 0 #SPI Chip Select pin. Valid values are 0 or 1
irqPin = 5 #DIO0 of sx127x and DIO1 of sx126x, used for IRQ in rx

# Settings valid only for SX126x. Default pin assignment refers to the PCB schematic /doc/LoRa_RPi_Companion_2022.pdf
resetPin = 6
busyPin = 4
txenPin = 0 #In Ebyte modules, it's used for switching on the tx pa.
rxenPin = 1 #In Ebyte modules, it's used for switching on the rx lna

## LoRa Settings valid for both SX127x and SX126x modules
frequency = 433775000 #frequency in Hz
preamble = 8 #valid preable lenght is 8/16/24/32
spreadingFactor = 12 #valid spreading factor is between 5 and 12
bandwidth = 125000 #possible BW values: 7800, 10400,15600, 20800, 31250, 41700, 62500, 125000, 250000, 500000
codingrate = 5 #valid code rate denominator is between 5 and 8
appendSignalReport = True #append signal report when packets are forwarded to aprs server
outputPower = 17 #maximum TX power is 22(22dBm) for SX126x, and 15 (17dBm) for SX127x . Higher values will be forced to max allowed!
TX_OE_Style = True #if True, tx RF packets are in OE Style, otherwise in standard AX25
#sync_word = 0x1424 #sync word is x4y4. Es: 0x12 of 1st gen LoRa chip --> 0x1424 of 2nd gen LoRa chip
sync_word = 0x12

#LoRa Settings valid only for SX126x
RX_GAIN_POWER_SAVING = False #If false, receiver is set in boosted gain mode (needs more power)
