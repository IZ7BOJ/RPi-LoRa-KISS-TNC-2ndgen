## Config file for RPi-LoRa-KISS-TNC 2nd generation

##Log enable and path
log_enable = True
logpath='/var/log/lora/lora.log' #log filename. Give r/w permission!

## KISS Settings
# Where to listen?
#	TCP_HOST can be "localhost", "0.0.0.0" or a specific interface address
#	TCP_PORT as configured in aprx.conf <interface> section
TCP_HOST = "0.0.0.0"
TCP_PORT = 10001

## Hardware settings
# Begin LoRa radio and set NSS, reset, busy, IRQ, txen, and rxen pin with connected Raspberry Pi gpio pins
# IRQ pin must be used, otherwise this software doesn't work (cannot be set to -1).
# txen and rxen pin are not used by this software so are set to -1

busId = 0 #SPI Bus ID. Must be enabled on raspberry (sudo raspi-config). Default is 0
csId = 0 #SPI Chip Select pin. Valid values are 0 or 1
resetPin = 22
busyPin = 23
irqPin = 26
txenPin = -1 #txenPin = 5
rxenPin = -1 #rxenPin = 25

## LoRa Settings (only most used, the others are left by default)
frequency = 433775000 #frequency in Hz
preamble = 8 #valid preable lenght is 8/16/24/32
spreadingFactor = 12 #valid spreading factor is between 5 and 12
bandwidth = 125000 #possible BW values: 7800, 10400,15600, 20800, 31250, 41700, 62500, 125000, 250000, 500000
codingrate = 5 #valid code rate denominator is between 4 and 8
appendSignalReport = True #append signal report when packets are forwarded to aprs server
outputPower = 0 #maximum TX power is 22(dBm)
TX_OE_Style = True #if True, tx RF packets are in OE Style, otherwise in standard AX25
sync_word = 0x1424 #sync word is x4y4. Es: 0x12 of 1st gen LoRa chip --> 0x1424 of 2nd gen LoRa chip
payloadLength = 50 #max payload length
crcType = False #crc check
RX_GAIN_POWER_SAVING = False #If false, receiver is set in boosted gain mode (consume more power)
