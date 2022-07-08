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

# Imports the necessary libraries...
import math
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import config

class display:

  def __init__(self):
    # init I2C
    self.i2c = board.I2C()
    self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, self.i2c, addr=0x3c)

    # Clear display.
    self.clear()

    # Load font and size.
    self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", config.font_size)

  def clear(self):
    # Create blank image for drawing.
    self.image = Image.new("1", (self.oled.width, self.oled.height))
    self.draw = ImageDraw.Draw(self.image)
    self.oled.fill(0)
    self.oled.show()

  def showtext(self,row):
    self.clear()
    r = math.ceil(self.draw.textsize(row,self.font)[0]/128) #calculate number of rows
    pos = int(128*len(row)/self.draw.textsize(row,self.font)[0])-1 #calculate number of characters in one row
    rows = [] #create list of rows
    for i in range(r) :
       rows.append(row[:pos])
       row=row[pos:]

    row="\n".join(rows)

    self.draw.text((0, 0), row, font=self.font, fill=255)
    self.oled.image(self.image)
    self.oled.show()

  def showimage(self,image):
    self.clear()
    self.oled.image(image)
    self.oled.show()
