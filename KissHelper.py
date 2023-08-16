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


# This program provides basic KISS AX.25 APRS frame encoding and decoding.
# Note that only APRS relevant structures are tested. It might not work
# for generic AX.25 frames.
#
# Inspired by:
# * Python script to decode AX.25 from KISS frames over a serial TNC
#   https://gist.github.com/mumrah/8fe7597edde50855211e27192cce9f88
#
# * Sending a raw AX.25 frame with Python
#   https://thomask.sdf.org/blog/2018/12/15/sending-raw-ax25-python.html
#
#   KISS-TNC for LoRa radio modem
#   https://github.com/IZ7BOJ/RPi-LoRa-KISS-TNC

import struct
import datetime
import config

KISS_FEND = 0xC0  # Frame start/end marker
KISS_FESC = 0xDB  # Escape character
KISS_TFEND = 0xDC  # If after an escape, means there was an 0xC0 in the source message
KISS_TFESC = 0xDD  # If after an escape, means there was an 0xDB in the source message

# APRS data types
DATA_TYPES_POSITION = b"!'/@`"
DATA_TYPE_MESSAGE = b":"
DATA_TYPE_THIRD_PARTY = b"}"

def logf(message):
    timestamp = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S - ')
    if config.log_enable:
       fileLog = open(config.logpath,"a")
       fileLog.write(timestamp + message+"\n")
       fileLog.close()
    print(timestamp + message)

# from LoRa OE_Style to KISS
# Addresses must be 6 bytes plus the SSID byte, each character shifted left by 1
# If it's the final address in the header, set the low bit to 1
# If it has been digipeated, set the H bit to 1
# Ignoring command/response for simple example
def encode_address(s, final):
    H=0b00000000 #default H bit low
    if chr(s[-1])=='*': #example: WIDE1-1* or WIDE1*
        s=s[:-1]
        H=0b10000000
    if b"-" not in s:
        s = s + b"-0"  # default to SSID 0
    call, ssid = s.split(b'-')
    if len(call) < 6:
        call = call + b" "*(6 - len(call)) # pad with spaces
    encoded_call = [x << 1 for x in call[0:6]]
    encoded_ssid = (int(ssid) << 1) | H | 0b01100000 | (0b00000001 if final else 0)
    return encoded_call + [encoded_ssid]


def decode_address(data, cursor):
    (a1, a2, a3, a4, a5, a6, a7) = struct.unpack("<BBBBBBB", data[cursor:cursor + 7])
    hrr = a7 >> 5
    ssid = (a7 >> 1) & 0xf
    ext = a7 & 0x1
    addr = struct.pack("<BBBBBB", a1 >> 1, a2 >> 1, a3 >> 1, a4 >> 1, a5 >> 1, a6 >> 1)
    if ssid != 0:
        call = addr.strip() + "-{}".format(ssid).encode()
    else:
        call = addr
    return (call, hrr, ext)

def ax25parser(frame): #extracts fields from ax25 frames and add signal report do payload, if specified
    pos = 0

    # DST
    (dest_addr, dest_hrr, dest_ext) = decode_address(frame, pos)
    pos += 7
    #print("DST: ", dest_addr)

    # SRC
    (src_addr, src_hrr, src_ext) = decode_address(frame, pos)
    pos += 7
    #print("SRC: ", src_addr)

    # REPEATERS
    ext = src_ext
    rpt_list = b""
    while ext == 0:
        rpt_addr, rpt_hrr, ext = decode_address(frame, pos)
        if rpt_hrr==b'111': # H bit high-->packet has been digipeated
           rpt_addr+=b'*'
        rpt_list += b","+rpt_addr
        #print("RPT: ", rpt_addr)
        pos += 7

    # CTRL
    ctrl = frame[pos]
    pos += 1
    if (ctrl & 0x3) == 0x3:
        #(pid,) = struct.unpack("<B", frame[pos])
        pid = frame[pos]
        #print("PID: "+str(pid))
        pos += 1
    elif (ctrl & 0x3) == 0x1:
        # decode_sframe(ctrl, frame, pos)
        logf("SFRAME")
        return None
    elif (ctrl & 0x1) == 0x0:
        # decode_iframe(ctrl, frame, pos)
        logf("IFRAME")
        return None
    payload=frame[pos:]
    dti=bytes(chr(payload[0]),'utf-8')
    logf("Extracted AX25 parameters from AX25 Frame")
    logf("From: "+repr(src_addr)[2:-1]+" To: "+repr(dest_addr)[2:-1]+" Via: "+repr(rpt_list)[3:-1]+" PID: "+str(hex(pid))+" Payload: "+str(payload)[str(payload).find("'"):-1])

    return src_addr,dest_addr,rpt_list,payload, dti

def encode_kiss_AX25(frame,signalreport): #from Lora to Kiss, Standard AX25

    src_addr,dest_addr,rpt_list,payload,dti=ax25parser(frame) #only for logging

    # Escape the packet in case either KISS_FEND or KISS_FESC ended up in our stream
    if config.appendSignalReport and str(dti) != DATA_TYPE_MESSAGE:
        frame += b" "+str.encode(signalreport,'utf-8')

    packet_escaped = []
    for x in frame:
        if x == KISS_FEND:
            packet_escaped += [KISS_FESC, KISS_TFEND]
        elif x == KISS_FESC:
            packet_escaped += [KISS_FESC, KISS_TFESC]
        else:
            packet_escaped += [x]

    # Build the frame that we will send to aprx and turn it into a string
    kiss_cmd = 0x00  # Two nybbles combined - TNC 0, command 0 (send data)
    kiss_frame = [KISS_FEND, kiss_cmd] + packet_escaped + [KISS_FEND]

    try:
        output = bytearray(kiss_frame)
    except ValueError:
        logf("Invalid value in frame.")
        return None
    return output

def encode_kiss_OE(frame,signalreport): #from Lora to Kiss, OE_Style
    # Ugly frame disassembling
    if not b":" in frame:
        logf("Can't decode OE LoRa Frame")
        return None
    path = frame.split(b":")[0]
    payload = frame[frame.find(b":")+1:]
    dti = bytes(chr(payload[0]),'utf-8')
    src_addr = path.split(b">")[0]
    digis = path[path.find(b">") + 1:].split(b",")
    dest_addr = digis.pop(0)

    # destination address
    packet = encode_address(dest_addr.upper(), False)
    # source address
    packet += encode_address(src_addr.upper(), len(digis) == 0)
    # digipeaters
    for digi in digis:
        final_addr = digis.index(digi) == len(digis) - 1
        packet += encode_address(digi.upper(), final_addr)
    # control field
    packet += [0x03]  # This is an UI frame
    # protocol ID
    packet += [0xF0]  # No protocol
    # information field
    logf("Extracted AX25 parameters from OE LoRa Frame")
    logf("From: "+repr(src_addr)[2:-1]+" To: "+repr(dest_addr)[2:-1]+" Via: "+str(digis)[1:-1].replace("b","").replace("'","")+" Payload: "+repr(payload)[2:-1])
    packet += payload
    if config.appendSignalReport and str(dti) != DATA_TYPE_MESSAGE:
        #some SW (es OE5BPA) append newline character at the end of packet. Must be cut for appending signal report
        if chr(packet[-1])=="\n":
          packet=packet[:-1]
        packet += b" "+str.encode(signalreport,'utf-8')

    # Escape the packet in case either KISS_FEND or KISS_FESC ended up in our stream
    packet_escaped = []
    for x in packet:
        if x == KISS_FEND:
            packet_escaped += [KISS_FESC, KISS_TFEND]
        elif x == KISS_FESC:
            packet_escaped += [KISS_FESC, KISS_TFESC]
        else:
            packet_escaped += [x]

    # Build the frame that we will send to Dire Wolf and turn it into a string
    kiss_cmd = 0x00  # Two nybbles combined - TNC 0, command 0 (send data)
    kiss_frame = [KISS_FEND, kiss_cmd] + packet_escaped + [KISS_FEND]
    try:
        #print(bytearray(kiss_frame).hex())
        output = bytearray(kiss_frame)
    except ValueError:
        logf("Invalid value in frame.")
        return None
    return output

def decode_kiss_OE(frame): #From Kiss to LoRa, OE_Style

    if frame[0] != 0xC0 or frame[len(frame) - 1] != 0xC0:
        logf("Kiss Header not found, abort decoding of Frame: "+repr(frame))
        return None
    frame=frame[2:len(frame) - 1] #cut kiss delimitator 0xc0 and command 0x00

    src_addr,dest_addr,rpt_list,payload,dti=ax25parser(frame) #only for logging

    #build OE_style frame piece by piece
    result = src_addr.strip()+b">"+dest_addr.strip()+rpt_list+b":"+payload
    return result

def decode_kiss_AX25(frame): #from kiss to LoRA, Standard AX25
    result = b""

    if frame[0] != 0xC0 or frame[len(frame) - 1] != 0xC0:
        logf("Kiss Header not found, abort decoding of Frame: "+repr(frame))
        return None
    frame=frame[2:len(frame) - 1] #cut kiss delimitator 0xc0 and command 0x00

    src_addr,dest_addr,rpt_list,payload,dti=ax25parser(frame) #only for logging

    return frame


class SerialParser():
    '''Simple parser for KISS frames. It handles multiple frames in one packet
    and calls the callback function on each frame'''
    STATE_IDLE = 0
    STATE_FEND = 1
    STATE_DATA = 2
    KISS_FEND = KISS_FEND

    def __init__(self, frame_cb=None):
        self.frame_cb = frame_cb
        self.reset()

    def reset(self):
        self.state = self.STATE_IDLE
        self.cur_frame = bytearray()

    def parse(self, data):
        #Call parse with a string of one or more characters
        for c in data:
            if self.state == self.STATE_IDLE:
                if c == self.KISS_FEND:
                    self.cur_frame.append(c)
                    self.state = self.STATE_FEND
            elif self.state == self.STATE_FEND:
                if c == self.KISS_FEND:
                    self.reset()
                else:
                    self.cur_frame.append(c)
                    self.state = self.STATE_DATA
            elif self.state == self.STATE_DATA:
                self.cur_frame.append(c)
                if c == self.KISS_FEND:
                    # frame complete
                    if self.frame_cb:
                        self.frame_cb(self.cur_frame)
                    self.reset()

if __name__ == "__main__":
    # Playground for testing

    kissframe = b"\xc0\x00\x82\xa0\xa4\xa6@@`\x9e\x8ar\xa8\x96\x90p\x88\x92\x8e\x92@@f\x88\x92\x8e\x92@@e\x03\xf0!4725.51N/00939.86E[322/002/A=001306 Batt=3.99V\xc0"

    #test decode KISS->OE
    print(decode_kiss_OE(kissframe))

    #test decode KISS->AX25
    print(decode_kiss_AX25(kissframe))

    #test encode OE->KISS
    OE_frame = b"OE9TKH-8>APRS,digi-3,digi-2:!4725.51N/00939.86E[322/002/A=001306 Batt=3.99V\n"
    signalreport="Level:-115dBm, SNR:0dB"
    print(encode_kiss_OE(OE_frame,signalreport))

    #test encode AX25->KISS
    ax25_frame = b"\x82\xa0\xa4\xa6@@`\x9e\x8ar\xa8\x96\x90p\x88\x92\x8e\x92@@f\x88\x92\x8e\x92@@e\x03\xf0!4725.51N/00939.86E[322/002/A=001306 Batt=3.99V\n"
    print(encode_kiss_AX25(ax25_frame,signalreport))
