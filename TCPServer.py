#!/usr/bin/python3
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

# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
from threading import Thread
import socket
from KissHelper import SerialParser
import KissHelper
import config
import datetime

def logf(message):
    timestamp = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S - ')
    if config.log_enable:
       fileLog = open(config.logpath,"a")
       fileLog.write(timestamp + message+"\r")
       fileLog.close()
    print(timestamp + message+"\r")

client_address = []
RECV_BUFFER_LENGTH = 1024

class KissServer(Thread):
    '''TCP Server to be connected by the APRS digipeater'''

    txQueue = None

    # host and port as configured in aprx/aprx.conf.lora-aprs < interface > section
    def __init__(self, txQueue, host="127.0.0.1", port=bytes(10001)):
        Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))
        self.socket.listen(1)
        self.data = str()
        self.txQueue = txQueue
        self.connection = None
        logf("KISS-Server: Started. Listening on IP "+host+" Port: "+str(port))

    def run(self):
        global client_address
        parser = SerialParser(self.queue_frame)
        while True:
            self.connection = None
            self.connection, client_address = self.socket.accept()
            parser.reset()
            logf("KISS-Server: Accepted Connection from %s" % client_address[0])
            while True:
                data = self.connection.recv(RECV_BUFFER_LENGTH)
                if data:
                    parser.parse(data)
                else:
                    logf("KISS-Server: Closed Connection from %s" % client_address[0])
                    self.connection.close()
                    break

    def queue_frame(self, frame, verbose=True):
        logf("Received from IP: "+str(client_address[0])+" KISS Frame: "+repr(frame))
        if config.TX_OE_Style:
            decoded_data = KissHelper.decode_kiss_OE(frame)
        else:
            decoded_data = KissHelper.decode_kiss_AX25(frame)
        #logf("Decapsulated Kiss Frame :"+ repr(decoded_data))

        self.txQueue.put(decoded_data, block=False)

    def __del__(self):
        self.socket.shutdown()

    def send(self, data,signalreport):
        global peer
        LORA_APRS_HEADER = b"<\xff\x01"
        # remove LoRa-APRS header if present
        if data[0:len(LORA_APRS_HEADER)] == LORA_APRS_HEADER:
            data = data[len(LORA_APRS_HEADER):]
            logf("\033[95mOE_Style header found!\033[0m")
            try:
                encoded_data = KissHelper.encode_kiss_OE(data,signalreport)
            except Exception as e:
                logf("KISS encoding went wrong (exception while parsing)")
                traceback.print_tb(e.__traceback__)
                encoded_data = None
        else:
            logf("\033[94mNo OE_Style header found, trying standard AX25 decoding...\033[0m")
            try:
                encoded_data = KissHelper.encode_kiss_AX25(data,signalreport)
            except Exception as e:
                logf("KISS encoding went wrong (exception while parsing)")
                traceback.print_tb(e.__traceback__)
                encoded_data = None
        if encoded_data != None:
            if self.connection:
                logf("Sending to ip: " + client_address[0] + " port:" + str(client_address[1]) + " Frame: " + repr(encoded_data))
                self.connection.sendall(encoded_data)
        else:
            logf("KISS encoding went wrong")


if __name__ == '__main__':
    '''Test program'''
    import time
    from multiprocessing import Queue

    TCP_HOST = "0.0.0.0"
    TCP_PORT = 10001

    # frames to be sent go here
    KissQueue = Queue()

    server = KissServer(KissQueue,TCP_HOST, TCP_PORT)
    server.setDaemon(True)
    server.start()

    #server.send(b"\xc0\x00\x82\xa0\xa4\xa6@@`\x9e\x8ar\xa8\x96\x90q\x03\xf0!4725.51N/00939.86E[322/002/A=001306 Batt=3.99V\xc0",{"level":0, "snr":0},'Level:-115dBm, SNR:0dB')
    server.send(b'<\xff\x01IZ7BOJ-12>APRS::OE1ACM-29: No GPS-Fix  Batt=0.00V {19','Level:-115dBm, SNR:0dB')
    data = KissQueue.get()
    print("Received KISS frame:" + repr(data))
