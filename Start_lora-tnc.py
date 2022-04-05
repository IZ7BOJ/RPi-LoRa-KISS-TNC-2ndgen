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
from LoraAprsKissTnc import LoraAprsKissTnc

print("########################\r")
print("\033[95m#LORA KISS TNC STARTING#\033[0m\r")
print("########################\r")
print("\r")
print("\033[1mCurrent LoRa init parameters:\033[0m\r")
print("\033[94mfrequency=\033[0m",config.frequency)
print("\033[94mpreamble=\033[0m",config.preamble)
print("\033[94mspreadingFactor=\033[0m",config.spreadingFactor)
print("\033[94mbandwidth=\033[0m",config.bandwidth)
print("\033[94mcodingrate=\033[0m",config.codingrate)
print("\033[94mappendSignalReport=\033[0m",config.appendSignalReport)
print("\033[94moutputPower=\033[0m",config.outputPower)
print("\033[94mTX_OE_Style=\033[0m",config.TX_OE_Style)
print("\033[94msync_word=\033[0m",hex(config.sync_word))
print("\033[94mRX_GAIN_POWER_SAVING=\033[0m",config.RX_GAIN_POWER_SAVING)
print("########################\r")
print("\r")

# TX KISS frames go here (Digipeater -> TNC)
kissQueue = Queue()

# KISSTCP Server for the digipeater to connect
server = KissServer(kissQueue, config.TCP_HOST, config.TCP_PORT)

server.setDaemon(True)
server.start()

# LoRa transceiver instance with all parameters
lora = LoraAprsKissTnc(kissQueue, server, config.busId, config.csId, config.resetPin, config.busyPin, config.irqPin, config.txenPin, config.rxenPin,
                       config.frequency, config.preamble, config.spreadingFactor, config.bandwidth, config.codingrate, config.appendSignalReport,
                       config.outputPower, config.sync_word, config.payloadLength, config.crcType, config.RX_GAIN_POWER_SAVING)

# this call loops forever inside
lora.startListening()
