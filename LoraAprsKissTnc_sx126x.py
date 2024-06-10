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
from display import display
from PIL import Image
from pathlib import Path

if config.disp_en:
   display = display()

def logf(message):
    timestamp = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S - ')
    if config.log_enable:
       fileLog = open(config.logpath,"a")
       fileLog.write(timestamp + message+"\n")
       fileLog.close()
    print(timestamp + message)

def lcd(message):
       timestamp = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S - ')
       display.showtext(timestamp + message)

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

        if config.disp_en:
           image = Image.open(str(Path(__file__).parent.absolute())+"/LoRa-KISS-TNC_logo_64x128_raw.ppm").convert("1")
           display.showimage(image)
           time.sleep(4)

        # Init SX126x as LoRA modem
        self.queue = queue
        self.server = server
        self.appendSignalReport = appendSignalReport

        if not self.begin(busId, csId, resetPin, busyPin, irqPin, txenPin, rxenPin) :
            raise Exception("Something wrong, can't begin LoRa radio")
        else :
            logf("LoRa radio initialized")
            if config.disp_en:
              lcd("LoRa radio initialized")

        # Configure LoRa to use TCXO with DIO3 as control
        if config.tcxo==True:
            self.setDio3TcxoCtrl(self.DIO3_OUTPUT_1_8, self.TCXO_DELAY_10)
            
        #Configure DIO2 as RF Switch if rxen and txen are not used
        if (config.rxenPin==-1 and config.txenPin==-1):
            self.setDio2RfSwitch(True)

        # Configure Frequency
        self.setFrequency(frequency)

        # Set RX gain. RX gain option are power saving gain or boosted gain
        if gain:
           self.setRxGain(self.RX_GAIN_POWER_SAVING)
        else:
          self.setRxGain(self.RX_GAIN_BOOSTED)

        # Set Low Data Rate Optimization starting from configured SF and BW.
        # Datasheet requires that it must be used when the symbol duration exceeds 16ms. This is the case below:
        # - SF=12 and 11 in 125 kHz.
        # - SF=12 in 250 kHz.
        if config.ldro=="": #ldro auto
            if (sf==12 and (bw==125000 or bw==250000))or(sf==11 and bw==125000): #symbol duration >16ms
                ldro=True
            else:
                ldro=False
        elif config.ldro != False or config.ldro != True: # if wrong values
            ldro = True #assign default value
        else:
            ldro = config.ldro #manual assignment from config.py                                                                            
        # Configure modulation parameter including spreading factor (SF), bandwidth (BW), and coding rate (CR)
        # Receiver must have same SF and BW setting with transmitter to be able to receive LoRa packet
        self.setLoRaModulation(sf, bw, cr, ldro)

        # Configure packet parameter including header type, preamble length, payload length, and CRC type
        # The explicit packet includes header contain CR, number of byte, and CRC type
        # Receiver can receive packet with different CR and packet parameters in explicit header mode
        self.setLoRaPacket(self.HEADER_EXPLICIT, preamble, payloadLength, crcType)

        self.setSyncWord(sync_word)

        #Set OCP to 140mA
        self.setCurrentProtection(0x38)

        # Set TX power, default power for SX1262 and SX1268 are +22 dBm and for SX1261 is +14 dBm
        # This function will set PA config with optimal setting for requested TX power
        self.setTxPower(outputPower, self.TX_POWER_SX1268)

        self.onReceive(self.callback) #callback function called after rx interrupt activation
        self.request(self.RX_CONTINUOUS) #Set receiver in continuous rx mode
     
    #Frequency offset register is not documented on Semtech datasheets.
    #This function is inspred from Radiolib (https://github.com/jgromes/RadioLib/blob/master/src/modules/SX126x.cpp)
    def getFreqError(self)  :
        state = self.readRegister(0x076B, 3)
        efe = (state[0]<<16 | state[1]<<8 | state[2]) & 0x0FFFFF
        #check the first bit
        if (efe & 0x80000) :
           efe = efe - (1<<20) #compute negative value
        error = 1.55 * efe / (1600 / (config.bandwidth/1000))
        return error

    def callback(self) :

      payload = [] #put received data into list of integers
      while self.available() >= 1 :
          payload.append(self.read())

      payload=bytes(payload) #int-->bytes
      if not payload:
            logf("No Payload!")
            return
      rssi = self.packetRssi()
      snr = self.snr()
      freq_err=self.getFreqError()
      signalreport = "Level:"+str(rssi)+" dBm, SNR:"+str(snr)+"dB"
      logf("LoRa RX[RSSI=%idBm, SNR=%.2fdB, %iBytes, Freq.Offset: %iHz]: %s" %(rssi, snr, len(payload), freq_err, repr(payload)))
      if config.disp_en:
         lcd("LoRa RX[RSSI=%idBm, SNR=%.2fdB, %iBytes, Freq.Offset: %iHz]: %s" %(rssi, snr, len(payload), freq_err, repr(payload)))

      # Show received status in case CRC or header error occur
      status = self.status()
      if status == self.STATUS_CRC_ERR :
         logf("CRC error, discarding frame...")
         return
      elif status == self.STATUS_HEADER_ERR :
         logf("Packet header error, discarding frame...")
         return
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
                               if config.disp_en:
                                  lcd("LoRa TX OE Syle packet: " + repr(data))
                            else:
                                logf("\033[95mLoRa TX Standard AX25 packet: \033[0m" + repr(data))
                                if config.disp_en:
                                  lcd("LoRa TX Standard AX25 packet: " + repr(data))
                            self.transmit(data)
                        except QueueEmpty:
                            pass
                time.sleep(0.50)
        except KeyboardInterrupt:
            logf("Keyboard Interrupt received. Exiting...")
            if config.disp_en:
              lcd("Keyboard Interrupt received. Exiting...")

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
