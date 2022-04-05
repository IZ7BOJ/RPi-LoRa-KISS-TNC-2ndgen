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
#   https://github.com/tomelec/RPi-LoRa-KISS-TNC

import struct
import datetime
import config

KISS_FEND = 0xC0  # Frame start/end marker
KISS_FESC = 0xDB  # Escape character
KISS_TFEND = 0xDC  # If after an escape, means there was an 0xC0 in the source message
KISS_TFESC = 0xDD  # If after an escape, means there was an 0xDB in the source message

def logf(message):
    timestamp = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S - ')
    if config.log_enable:
       fileLog = open(config.logpath,"a")
       fileLog.write(timestamp + message+"\r")
       fileLog.close()
    print(timestamp + message+"\r")

# Addresses must be 6 bytes plus the SSID byte, each character shifted left by 1
# If it's the final address in the header, set the low bit to 1
# Ignoring command/response for simple example
def encode_address(s, final):
    if b"-" not in s:
        s = s + b"-0"  # default to SSID 0
    call, ssid = s.split(b'-')
    if len(call) < 6:
        call = call + b" "*(6 - len(call)) # pad with spaces
    encoded_call = [x << 1 for x in call[0:6]]
    encoded_ssid = (int(ssid) << 1) | 0b01100000 | (0b00000001 if final else 0)
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


def encode_kiss_AX25(frame): #from Lora to Kiss, Standard AX25
    packet=frame #no manipulation needed in case of ax25 packets
    
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
    while ext == 0:
        rpt_addr, rpt_hrr, ext = decode_address(frame, pos)
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
        #print("SFRAME")
        return None
    elif (ctrl & 0x1) == 0x0:
        # decode_iframe(ctrl, frame, pos)
        #print("IFRAME")
        return None

    logf("Extracted AX25 parameters from AX25 LoRa Frame")
    logf("From: "+repr(src_addr)[2:-1]+" To: "+repr(dest_addr)[2:-1]+" Payload: "+repr(frame[pos:]))


    # Escape the packet in case either KISS_FEND or KISS_FESC ended up in our stream
    packet_escaped = []
    for x in packet:
        if x == KISS_FEND:
            packet_escaped += [KISS_FESC, KISS_TFEND]
        elif x == KISS_FESC:
            packet_escaped += [KISS_FESC, KISS_TFESC]
        else:
            packet_escaped += [x]

    # Build the frame that we will send via Kiss and turn it into a string
    kiss_cmd = 0x00  # Two nybbles combined - TNC 0, command 0 (send data)
    kiss_frame = [KISS_FEND, kiss_cmd] + packet_escaped + [KISS_FEND]
    try:
        output = bytearray(kiss_frame)
    except ValueError:
        logf("Invalid value in frame.")
        return None
    return output

def encode_kiss_OE(frame): #from Lora to Kiss, OE_Style
    # Ugly frame disassembling
    if not b":" in frame:
        return None
    path = frame.split(b":")[0]
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
    logf("From: "+repr(src_addr)[2:-1]+" To: "+repr(dest_addr)[2:-1]+" Payload: "+repr(frame[frame.find(b":") + 1:]))
    packet += frame[frame.find(b":") + 1:]

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
        output = bytearray(kiss_frame)
    except ValueError:
        logf("Invalid value in frame.")
        return None
    return output

def decode_kiss_OE(frame): #From Kiss to LoRa, OE_Style
    result = b""
    pos = 0
    if frame[pos] != 0xC0 or frame[len(frame) - 1] != 0xC0:
        print(frame[pos], frame[len(frame) - 1])
        return None
    pos += 1
    pos += 1

    # DST
    (dest_addr, dest_hrr, dest_ext) = decode_address(frame, pos)
    pos += 7
    #print("DST: ", dest_addr)

    # SRC
    (src_addr, src_hrr, src_ext) = decode_address(frame, pos)
    pos += 7
    #print("SRC: ", src_addr)

    result += src_addr.strip()
    # print(type(result), type(dest_addr.strip()))
    result += b">" + dest_addr.strip()

    # REPEATERS
    ext = src_ext
    while ext == 0:
        rpt_addr, rpt_hrr, ext = decode_address(frame, pos)
        #print("RPT: ", rpt_addr)
        pos += 7
        result += b"," + rpt_addr.strip()

    result += b":"

    # CTRL
    # (ctrl,) = struct.unpack("<B", frame[pos])
    ctrl = frame[pos]
    pos += 1
    if (ctrl & 0x3) == 0x3:
        #(pid,) = struct.unpack("<B", frame[pos])
        pid = frame[pos]
        # print("PID="+str(pid))
        pos += 1
        logf("Decapsulating KISS Frame and extracting ax25 fields...")
        logf("From: "+repr(src_addr)[2:-1]+" To: "+repr(dest_addr)[2:-1]+" Via: "+repr(rpt_addr)[2:-1]+" Payload: "+repr(frame[pos:len(frame) - 1]))
        result += frame[pos:len(frame) - 1]
    elif (ctrl & 0x3) == 0x1:
        # decode_sframe(ctrl, frame, pos)
        print("SFRAME")
        return None
    elif (ctrl & 0x1) == 0x0:
        # decode_iframe(ctrl, frame, pos)
        print("IFRAME")
        return None

    return result

def decode_kiss_AX25(frame): #from kiss to LoRA, Standard AX25
    result = b""
    pos = 0
    if frame[pos] != 0xC0 or frame[len(frame) - 1] != 0xC0:
        print(frame[pos], frame[len(frame) - 1])
        return None
    pos += 1
    pos += 1

    # DST
    (dest_addr, dest_hrr, dest_ext) = decode_address(frame, pos)
    pos += 7
    print("DST: ", dest_addr)

    # SRC
    (src_addr, src_hrr, src_ext) = decode_address(frame, pos)
    pos += 7
    print("SRC: ", src_addr)

    # REPEATERS
    ext = src_ext
    while ext == 0:
        rpt_addr, rpt_hrr, ext = decode_address(frame, pos)
        print("RPT: ", rpt_addr)
        pos += 7

    ctrl = frame[pos]
    pos += 1
    if (ctrl & 0x3) == 0x3:
        #(pid,) = struct.unpack("<B", frame[pos])
        pid = frame[pos]
        print("PID="+str(pid))
        pos += 1

    elif (ctrl & 0x3) == 0x1:
        # decode_sframe(ctrl, frame, pos)
        print("SFRAME")
        return None
    elif (ctrl & 0x1) == 0x0:
        # decode_iframe(ctrl, frame, pos)
        print("IFRAME")
        return None

    result = frame[2:len(frame) - 1] #Cut FEND and COMMAND bytes form kiss frame and transmit as is to RF
    return result


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

    #test decode
    kissframe = b"\xc0\x00\x82\xa0\xa4\xa6@@`\x9e\x8ar\xa8\x96\x90q\x03\xf0!4725.51N/00939.86E[322/002/A=001306 Batt=3.99V\xc0"
    print(decode_kiss_OE(kissframe))

    #test encode
    OE_frame = b"OE9TKH-8>APRS,digi-3,digi-2:!4725.51N/00939.86E[322/002/A=001306 Batt=3.99V"
    print(encode_kiss_OE(OE_frame))
