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
import sys
from asyncio import QueueEmpty
import traceback
sys.path.insert(0, './pySX127x/')
from pySX127x.SX127x.LoRa import LoRa
from pySX127x.SX127x.constants import *
from pySX127x.SX127x.board_config import BOARD
from display import display
from PIL import Image
from pathlib import Path

#import RPi.GPIO as GPIO
#import spidev

if config.disp_en:
   display = display()

def logf(message):
    timestamp = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S - ')
    if config.log_enable:
       fileLog = open(config.logpath,"a")
       fileLog.write(timestamp + message+"\n")
       fileLog.close()
    print(timestamp + message+"\n")

def lcd(message):
       timestamp = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S - ')
       display.showtext(timestamp + message)

class LoraAprsKissTnc(LoRa):
    LORA_APRS_HEADER = b"<\xff\x01"

    # APRS data types
    DATA_TYPES_POSITION = b"!'/@`"
    DATA_TYPE_MESSAGE = b":"
    DATA_TYPE_THIRD_PARTY = b"}"

    queue = None
    server = None

    # init has LoRa APRS default config settings - might be initialized different when creating object with parameters
    def __init__(self, queue, server, frequency=433775000, preamble=8, spreadingFactor=12, bandwidth=BW.BW125,
                 codingrate=5, crc = True, appendSignalReport = True, paSelect = 1, outputPower = 15, sync_word = 0x12, ldro=True, verbose=False):
    # Init SX127x
        if config.disp_en:
           image = Image.open(str(Path(__file__).parent.absolute())+"/LoRa-KISS-TNC_logo_64x128_raw.ppm").convert("1")
           display.showimage(image)
           time.sleep(4)

        BOARD.setup()

        logf("LoRa radio initialized. Waiting for LoRa Spots...")
        if config.disp_en:
           lcd("LoRa radio initialized. Waiting for LoRa Spots...")

        super(LoraAprsKissTnc, self).__init__(verbose)
        self.queue = queue
        self.appendSignalReport = appendSignalReport

        self.set_mode(MODE.SLEEP)
        frequency=frequency/1e6
        self.set_freq(frequency)
        self.set_preamble(preamble)
        self.set_spreading_factor(spreadingFactor)

        bw = {
        7800  : BW.BW7_8,
        10400 : BW.BW10_4,
        15600 : BW.BW15_6,
        20800 : BW.BW20_8,
        31250 : BW.BW31_25,
        41700 : BW.BW41_7,
        62500 : BW.BW62_5,
        125000: BW.BW125,
        250000: BW.BW250,
        500000: BW.BW500
        }

        self.set_bw(bw[bandwidth])

	# Set Low Data Rate Optimization starting from configured SF and BW.
        # Datasheet requires that it must be used when the symbol duration exceeds 16ms. This is the case below:
        # - SF=12 and 11 in 125 kHz.
        # - SF=12 in 250 kHz.
        if config.ldro=="": #ldro auto
            if (spreadingFactor==12 and (bandwidth==125000 or bandwidth==250000))or(spreadingFactor==11 and bandwidth==125000): #symbol duration >16ms
                ldro=True
            else:
                ldro=False
        else:
            ldro = config.ldro #manual assignment from config.py

        self.set_low_data_rate_optim(ldro)

        CR = {
        5 : CODING_RATE.CR4_5,
        6 : CODING_RATE.CR4_6,
        7 : CODING_RATE.CR4_7,
        8 : CODING_RATE.CR4_8
        }
        self.set_coding_rate(CR[codingrate])
        self.set_ocp_trim(100)

        self.set_sync_word(sync_word)
      
        self.set_rx_crc(crc)

        if outputPower>15 : outputPower=15
        self.set_pa_config(paSelect, 7, outputPower)
        self.set_max_payload_length(255)
        self.set_dio_mapping([0] * 6)
        self.server = server

        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        #self.set_mode(MODE.SLEEP)

    def startListening(self):
        try:
            while True:
                # only transmit if no signal is detected to avoid collisions
                if not self.get_modem_status()["signal_detected"]:
                    # print("RSSI: %idBm" % lora.get_rssi_value())
                    # FIXME: Add noise floor measurement for telemetry
                    if not self.queue.empty():
                        try:
                            data = self.queue.get(block=False)
                            #if self.aprs_data_type(data) == self.DATA_TYPE_THIRD_PARTY:
                                # remove third party thing
                                #data = data[data.find(self.DATA_TYPE_THIRD_PARTY) + 1:]
                            if config.TX_OE_Style:
                                data = self.LORA_APRS_HEADER + data
                                logf("LoRa TX OE Syle packet: " + repr(data))
                                if config.disp_en:
                                   lcd("LoRa TX OE Syle packet: " + repr(data))
                            else:
                                logf("LoRa TX Standard AX25 packet: " + repr(data))
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
            BOARD.teardown()
    def twos_comp(self,val, bits):
        """compute the 2's complement of int value val"""
        if (val & (1 << (bits - 1))) != 0: # if sign bit is set
            val = val - (1 << bits)        # compute negative value
        return val                         # else return positive value as is

    def on_rx_done(self):
        payload = self.read_payload(nocheck=True)
        if not payload:
            logf("No Payload!")
            return
        rssi = self.get_pkt_rssi_value()
        snr = self.get_pkt_snr_value()
        freq_err = self.twos_comp(self.get_fei(),20)*pow(2,24)/32e6*config.bandwidth/1000/500
        signalreport = "Level:"+str(rssi)+" dBm, SNR:"+str(snr)+"dB"
        data = bytes(payload)
        logf("LoRa RX[%idBm/%.2fdB, %iHz ,%ibytes]: %s" %(rssi, snr, freq_err, len(data), repr(data)))
        if config.disp_en:
           lcd("LoRa RX[%idBm/%.2fdB, %iHz ,%ibytes]: %s" %(rssi, snr, freq_err, len(data), repr(data)))

        flags = self.get_irq_flags()
        if any([flags[s] for s in ['crc_error', 'rx_timeout']]):
            logf("Receive Error, discarding frame.")
            # print(self.get_irq_flags())
            self.clear_irq_flags(RxDone=1, PayloadCrcError=1, RxTimeout=1)  # clear rxdone IRQ flag
            self.reset_ptr_rx()
            self.set_mode(MODE.RXCONT)
            return

        if self.server:
            self.server.send(data, signalreport)
        self.clear_irq_flags(RxDone=1)  # clear rxdone IRQ flag
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    # self.set_mode(MODE.CAD)

    def on_tx_done(self):
        logf("TX DONE")
        self.clear_irq_flags(TxDone=1)  # clear txdone IRQ flag
        self.set_dio_mapping([0] * 6)
        self.set_mode(MODE.RXCONT)

    def transmit(self, data):
        self.write_payload([c for c in data])
        self.set_dio_mapping([1, 0, 0, 0, 0, 0])
        self.set_mode(MODE.TX)

    def aprs_data_type(self, lora_aprs_frame):
        delimiter_position = lora_aprs_frame.find(b":")
        try:
            return lora_aprs_frame[delimiter_position + 1]
        except IndexError:
            return ""
            
