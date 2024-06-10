#!/usr/bin/python3
# -*- coding: utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Usage: python3 Start_lora-tnc.py
#
from queue import Queue
from TCPServer import KissServer
import config
if config.sx127x:
   from LoraAprsKissTnc_sx127x import LoraAprsKissTnc
else:
   from LoraAprsKissTnc_sx126x import LoraAprsKissTnc

print("########################\r")
print("#LORA KISS TNC STARTING#\r")
print("########################\r")
print("#Lora parameters:\r")
print("frequency=",config.frequency)
print("preamble=",config.preamble)
print("spreadingFactor=",config.spreadingFactor)
print("bandwidth=",config.bandwidth)
print("codingrate=",config.codingrate)
print("APPEND_SIGNAL_REPORT=",config.appendSignalReport)
print("outputPower=",config.outputPower)
print("TX_OE_Style=",config.TX_OE_Style)
print("sync_word=",hex(config.sync_word))
print("crc=",config.crc)
print("########################\r")

# TX KISS frames go here (Digipeater -> TNC)
kissQueue = Queue()

# KISSTCP Server for the digipeater to connect
server = KissServer(kissQueue, config.TCP_HOST, config.TCP_PORT)

server.setDaemon(True)
server.start()

if config.sx127x:
   # LoRa transceiver instance
   lora = LoraAprsKissTnc(kissQueue, server, config.frequency, config.preamble, config.spreadingFactor, config.bandwidth, config.codingrate, config.crc, config.appendSignalReport, 1, config.outputPower, config.sync_word, config.ldro)
else:
   lora = LoraAprsKissTnc(kissQueue, server, config.busId, config.csId, config.resetPin, config.busyPin, config.irqPin, config.txenPin, config.rxenPin,
                       config.frequency, config.preamble, config.spreadingFactor, config.bandwidth, config.codingrate, config.appendSignalReport,
                       config.outputPower, config.sync_word, 80, config.crc, config.RX_GAIN_POWER_SAVING, config.ldro)
#print(lora)

# this call loops forever inside
lora.startListening()
