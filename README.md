# WiPy-2.0-LCD
Controlling a HD44780 compliant LCD display connected to a WiPy 2.0 via I2C.

### Summary
LCD displays in 16x2 or 20x4 format are abundant. Combine them with an I2C backpack and by using only two pins your WiPy can output text. Unfortunately you can't just send characters to the display. A special protocol is required. File *i2c_lcd.py* contains class *LCD()* which handles the complexities of communicating with the display for you. See *lcd_test.py* for an example how to use class LCD.

### Backgroud
There are several universal libraries to control displays attached to all different kinds of hardware. However providing a universal solution sometimes makes the software quite difficult to understand for beginners like me. Having problems getting them to work on my WiPy 2.0 I created this package with the aim to provide an - as simple as possible - example how to control a display.

### Hardware
The backpacks are based on I2C port expanders like the PCF8574. These provide an 8-bit output port. The LCD display has an 8-bit databus, but also needs 3 additional control signals so you would actually need an 11-bit port on the expander. To cope with this the display must be used in 4-bit mode. This means all data bytes are transferred as 2 separate nibbles using only the high part of the displays' databus (D4-D7). These pins are connected to D4 to D7 of the port expander, leaving the expanders lower D0 to D3 pins free for the control signals. On the version of the backpack I have (see image [expander.png](https://github.com/erikdelange/WiPy-2.0-LCD/blob/master/images/expander.png)) the connections are as follows:

PCF8574 Bit | LCD display signal | LCD display pin
------------|--------------------|----------------
0 | Register Select (RS) | 4
1 | Read/Write (RW) | 5
2 | Enable (E) | 6
3 | Backlight (B) |
4 | DB4 | 11
5 | DB5 | 12
6 | DB6 | 13
7 | DB7 | 14

I've read that sometimes the control signals are wired differently i.e. the pins from the port expander are connected to other pins on the display then indicated in the table above. With a bit of effort you can figure out the actual connections yourself. Programatically toggle a single bit on the port expander xontinuously with an interval of +/- 5 seconds. Use a voltmeter to check each pin on the display in turn to figure out which one is constantly changing. Toggling a bit is done by writing the appropriate mask to the port expander, wait 5 seconds and then write all zero's. For example if you want to switch on bit 2 then write 0x04 (0b0000100) to the port expander. If the connections do not match you do have to modify the masks class LCD().

The backpack can be soldered directly on the display. However you can't connect it directly to the WiPy as the display requires 5V logic signals and the WiPy works on 3.3V. An I2C level [converter](https://github.com/erikdelange/WiPy-2.0-LCD/blob/master/images/converter.png) **must** be placed between the WiPy and the backpack. See image converter.png for the one I have used. This one has built-in pull-up resistors so I only needed some wires. The converter requires a 5V and 3.3V supply which can both be taken from the WiPy. The display can also be provided with 5V by the WiPy Expansion Board (Vin).

I used a breadboard to hold the I2C level converter. There's al lot of wires around (see image [board.png](https://github.com/erikdelange/WiPy-2.0-LCD/blob/master/images/board.png)). Make sure they are connected properly, especialy the 5V and 3.3V lines and ground. Check them all 3 times because a mistake may damage your WiPy! Also do not forget to remove the LED jumper from your expansion board. The LED is connected to P9 (expansion board G16) which now must be used as the I2C SDA signal. Port P10 (expansion board G17) is the I2C SCL signal.

### Software
Each I2C device has an address. You first have to figure what the address of your port expander is. The scan() function in WiPy's I2C library does just this. Connect the backpack to the converter, and the converter to the WiPy and then run scan() as is shown below. If everything is connected OK you will receive an address (most often 0x27 or 39 decimal).
```python
>>> from machine import I2C
>>> i2c = I2C(0, I2C.MASTER)
>>> i2c.scan()
[39]
```
Data (like character 'A') is sent to the display in two steps; first the high nibble then the low nibble. Because the display works in 4-bit mode and its inputs DB4-7 are connected to pins 4-7 of the port expander all data must be placed in the high nibble when sending via I2C. So in order to send the lower nibble of the data byte it must first be shifted 4 position left into the high nibble. The corresponding function looks like this:
```python
def write_command(self, cmd):
    self.write_byte(cmd & 0xF0)
    self.write_byte((cmd << 4) & 0xF0)
```
The lower nibbles are masked so they are always zero and used to transport control signals like enable. Data is accepted by the LCD display when the enable bit changes from high to low. The code below seems to transfer data twice, however the first time the enable signal is high (set via MASK_EN), and the second time it is low, thus triggering the read action by the display.
```python
def write_byte(self, byte):
    self.i2c.writeto(self.addr, bytes([byte | self.MASK_EN]))
    self.i2c.writeto(self.addr, bytes([byte]))
```
### Additional information

* The I2C backpack I've been using can be found [here](https://www.hobbyelectronica.nl/product/i2c-lcd-interface-voor-16x2-en-20x4-displays/).

* The I2C level converter I've been using can be found [here](https://www.hobbyelectronica.nl/product/i2c-level-conversie-module-5v-naar-3v/).

* Interesting C-Libraries with LCD drivers can be found [here](http://arduino-info.wikispaces.com/LCD-Blue-I2C).

* The datasheet for the LCD controller can be found [here](https://www.sparkfun.com/datasheets/LCD/HD44780.pdf).

* Details on the controllers memory layout for various display sizes can be found [here](http://irtfweb.ifa.hawaii.edu/~tcs3/tcs3/vendor_info/Technologic_systems/embeddedx86/HD44780_LCD/lcd0.shtml.htm).
