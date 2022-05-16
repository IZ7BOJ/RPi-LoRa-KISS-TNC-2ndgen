#!/usr/bin/python
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

import datetime
import time
import config
import os
import sys
from asyncio import QueueEmpty
import traceback
currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(currentdir)))
from LoRaRF import SX126x

#from pySX127x.SX127x.board_config import BOARD

#import KissHelper

def logf(message):
    timestamp = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S - ')
    if config.log_enable:
       fileLog = open(config.logpath,"a")
       fileLog.write(timestamp + message+"\n")
       fileLog.close()
    print(timestamp + message+"\n")

class LoraAprsKissTnc(SX126x): #Inheritance of SX126x class
    LORA_APRS_HEADER = b"<\xff\x01"

    # APRS data types
    DATA_TYPES_POSITION = b"!'/@`"
    DATA_TYPE_MESSAGE = b":"
    DATA_TYPE_THIRD_PARTY = b"}"

    queue = None
    server = None

    # init has LoRa APRS default config settings - might be initialized different when creating object with parameters
    def __init__(self, queue, server, busId=0, csId=0, resetPin=22, busyPin=23, irqPin=26, txenPin=-1, rxenPin=-1,
                frequency=433775000, preamble=8, sf=12, bw=125000, cr=5, appendSignalReport=True, outputPower=22,
                sync_word=0x1424, payloadLength=50, crcType=False, gain=False):

        # Init SX126x as LoRA modem
        #BOARD.setup()
        self.queue = queue
        self.server = server
        self.appendSignalReport = appendSignalReport

        if not self.begin(busId, csId, resetPin, busyPin, irqPin, txenPin, rxenPin) :
            raise Exception("Something wrong, can't begin LoRa radio")
        else :
            logf("LoRa radio initialized")

        # Configure LoRa to use TCXO with DIO3 as control
        self.setDio3TcxoCtrl(self.DIO3_OUTPUT_1_8, self.TCXO_DELAY_10)

        # Configure Frequency
        self.setFrequency(frequency)

        # Set RX gain. RX gain option are power saving gain or boosted gain
        if gain:
           self.setRxGain(self.RX_GAIN_POWER_SAVING)
        else:
          self.setRxGain(self.RX_GAIN_BOOSTED)

        # Configure modulation parameter including spreading factor (SF), bandwidth (BW), and coding rate (CR)
        # Receiver must have same SF and BW setting with transmitter to be able to receive LoRa packet
        self.setLoRaModulation(sf, bw, cr, True) #final True is LDRO, must be set

        # Configure packet parameter including header type, preamble length, payload length, and CRC type
        # The explicit packet includes header contain CR, number of byte, and CRC type
        # Receiver can receive packet with different CR and packet parameters in explicit header mode
        self.setLoRaPacket(self.HEADER_EXPLICIT, preamble, payloadLength, crcType)

        self.setSyncWord(sync_word)

        # Set TX power, default power for SX1262 and SX1268 are +22 dBm and for SX1261 is +14 dBm
        # This function will set PA config with optimal setting for requested TX power
        self.setTxPower(outputPower, self.TX_POWER_SX1268)

        self.onReceive(self.callback) #callback function called after rx interrupt activation
        self.request(self.RX_CONTINUOUS) #Set receiver in continuous rx mode

    def callback(self) :

      payload = [] #put received data into list of integers
      while self.available() > 1 :
          payload.append(self.read())

      payload=bytes(payload) #int-->bytes
      if not payload:
            logf("No Payload!")
            return
      rssi = self.packetRssi()
      snr = self.snr()
      signalreport = "Level:"+str(rssi)+" dBm, SNR:"+str(snr)+"dB"
      logf("LoRa RX[RSSI=%idBm, SNR=%idB, %iBytes]: %s" %(rssi, snr, len(payload), repr(payload)))

      # Show received status in case CRC or header error occur
      status = self.status()
      if status == self.STATUS_CRC_ERR : logf("CRC error")
      if status == self.STATUS_HEADER_ERR : logf("Packet header error")

      if self.server:
            self.server.send(payload,signalreport)

    def startListening(self):
        try:
            while True:
                # only transmit if no signal is detected to avoid collisions
                if not self.busyCheck(1):
                    if not self.queue.empty():
                        try:
                            data = self.queue.get(block=False)
                            if config.TX_OE_Style:
                               if self.aprs_data_type(data) == self.DATA_TYPE_THIRD_PARTY:
                                   # remove third party thing in case of OE_Style tx
                                   data = data[data.find(self.DATA_TYPE_THIRD_PARTY) + 1:]
                               data = self.LORA_APRS_HEADER + data
                               logf("\033[94mLoRa TX OE Syle packet: \033[0m" + repr(data))
                            else:
                                logf("\033[95mLoRa TX Standard AX25 packet: \033[0m" + repr(data))
                            self.transmit(data)
                        except QueueEmpty:
                            pass
                time.sleep(0.50)
        except KeyboardInterrupt:
            #BOARD.teardown()
            logf("Keyboard Interrupt received. Exiting...")

    def transmit(self, data):

        messageList = list(data)
        for i in range(len(messageList)) : messageList[i] = int(messageList[i])
        # write() method must be placed between beginPacket() and endPacket()
        self.beginPacket()
        self.write(messageList, len(messageList))
        self.endPacket()
        self.wait() # Wait until modulation process for transmitting packet finish
        self.request(self.RX_CONTINUOUS) #Request for receiving new LoRa packet in RX continuous mode

    def aprs_data_type(self, lora_aprs_frame):
        delimiter_position = lora_aprs_frame.find(b":")
        try:
            return bytes([lora_aprs_frame[delimiter_position + 1]])
        except IndexError:
            return ""
