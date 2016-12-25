from utime import sleep_ms


class LCD():
	"""	Control a HD44780 compliant LCD module connected to a WiPy 2.0 via I2C.

		The LCD's 16 pins are connected to an (PCF8574) I2C port expander.
		LCD access is in 4-bit mode (using the upper nibble of the data byte).

		PCF8574 bit		LCD module pin
			0				4		Register Select (RS)
			1				5		Read/Write (RW)
			2				6		Enable (EN)
			3				-		Backlight On/Off
		  4 - 7			  11-14		DB 4-7
	"""

	# HD44780 LCD controller commands
	LCD_CLEARDISPLAY = 0x01
	LCD_RETURNHOME = 0x02
	LCD_ENTRYMODESET = 0x04
	LCD_DISPLAYCONTROL = 0x08
	LCD_CURSORSHIFT = 0x10
	LCD_FUNCTIONSET = 0x20
	LCD_SETCGRAMADDR = 0x40
	LCD_SETDDRAMADDR = 0x80

	# flags for display entry mode
	LCD_ENTRYRIGHT = 0x00
	LCD_ENTRYLEFT = 0x02
	LCD_ENTRYSHIFTINCREMENT = 0x01
	LCD_ENTRYSHIFTDECREMENT = 0x00

	# flags for display and cursor control
	LCD_DISPLAYON = 0x04
	LCD_DISPLAYOFF = 0x00
	LCD_CURSORON = 0x02
	LCD_CURSOROFF = 0x00
	LCD_BLINKON = 0x01
	LCD_BLINKOFF = 0x00

	# flags for display and cursor shift
	LCD_DISPLAYMOVE = 0x08
	LCD_CURSORMOVE = 0x00
	LCD_MOVERIGHT = 0x04
	LCD_MOVELEFT = 0x00

	# flags for function set
	LCD_4BITMODE = 0x00
	LCD_8BITMODE = 0x10
	LCD_1LINE = 0x00
	LCD_2LINE = 0x08
	LCD_5x8DOTS = 0x00
	LCD_5x10DOTS = 0x04
	LCD_RESET = 0x30

	MASK_RS = 0x01
	MASK_RW = 0x02
	MASK_EN = 0x04

	LCD_BACKLIGHTON = 0x08
	LCD_BACKLIGHTOFF = 0x00

	def __init__(self, i2c, addr, lines, columns, dots=LCD_5x8DOTS):
		"""	Perform initialization as specified in HD44780 datasheet. """

		# note: no checks on impossible line and column combinations
		self._i2c = i2c
		self._addr = addr
		self._lines = lines
		self._columns = columns
		self._backlight = self.LCD_BACKLIGHTOFF
		self._display = self.LCD_DISPLAYOFF | self.LCD_CURSOROFF | self.LCD_BLINKOFF
		self._x = 0
		self._y = 0

		self._i2c.writeto(self._addr, bytes([0x00]))
		sleep_ms(50)
		self._write_init_nibble(self.LCD_RESET)
		sleep_ms(5)
		self._write_init_nibble(self.LCD_RESET)
		sleep_ms(1)
		self._write_init_nibble(self.LCD_RESET)
		sleep_ms(1)
		# display now in 8-bit mode
		self._write_init_nibble(self.LCD_FUNCTIONSET | self.LCD_4BITMODE)
		# display now in 4-bit mode
		if self._lines == 1:
			self._write_command(self.LCD_FUNCTIONSET | self.LCD_1LINE | dots)
		else:
			self._write_command(self.LCD_FUNCTIONSET | self.LCD_2LINE | dots)
		# now lines and font size cannot be changed anymore
		self._write_command(self.LCD_DISPLAYCONTROL | self._display)
		self._write_command(self.LCD_CLEARDISPLAY)
		self._write_command(self.LCD_ENTRYMODESET | self.LCD_ENTRYLEFT | self.LCD_ENTRYSHIFTDECREMENT)
		# all steps from initializing by instruction now completed
		self.display_on()
		self.backlight_on()

	def clear(self):
		"""	Clear LCD and move cursor to top-left. """
		self._write_command(self.LCD_CLEARDISPLAY)
		self._write_command(self.LCD_RETURNHOME)
		self._x = self._y = 0

	def display_on(self):
		""" Turn on (i.e. unblank) the LCD. """
		self._display |= self.LCD_DISPLAYON
		self._write_command(self.LCD_DISPLAYCONTROL | self._display)

	def display_off(self):
		""" Turn off (i.e. blank) the LCD. """
		self._display &= ~self.LCD_DISPLAYON
		self._write_command(self.LCD_DISPLAYCONTROL | self._display)

	def cursor_on(self):
		""" Make the cursor visible. """
		self._display |= self.LCD_CURSORON
		self._write_command(self.LCD_DISPLAYCONTROL | self._display)

	def cursor_off(self):
		""" Hide the cursor. """
		self._display &= ~self.LCD_CURSORON
		self._write_command(self.LCD_DISPLAYCONTROL | self._display & ~self.LCD_BLINKON)

	def blink(self):
		""" Make the cursor blink. Implicitly makes cursor visible. """
		self._display |= self.LCD_BLINKON | self.LCD_CURSORON
		self._write_command(self.LCD_DISPLAYCONTROL | self._display)

	def solid(self):
		""" Make the cursor solid. Implicitly makes cursor visible. """
		self._display &= ~self.LCD_BLINKON | self.LCD_CURSORON
		self._write_command(self.LCD_DISPLAYCONTROL | self._display)

	def backlight_on(self):
		"""	Turn on the backlight. """
		self._backlight = self.LCD_BACKLIGHTON
		self._i2c.writeto(self._addr, bytes([self.LCD_BACKLIGHTON]))

	def backlight_off(self):
		"""	Turn off the backlight. """
		self._backlight = self.LCD_BACKLIGHTOFF
		self._i2c.writeto(self._addr,  bytes([self.LCD_BACKLIGHTOFF]))

	def move_to(self, x, y):
		""" Move the cursor to the indicated position. (0,0 is top left). """
		self._x = x if x < self._columns else self._columns - 1
		self._y = y if y < self._lines else self._lines - 1
		address = self._x & 0x3F
		if self._y & 1:
			address += 0x40	 # For lines 1 & 3 offset is 0x40
		if self._y & 2:
			address += 0x14  # For lines 2 & 4 offset is 0x14
		self._write_command(self.LCD_SETDDRAMADDR | address)

	def putch(self, ch):
		""" Write ch to the LCD and advance cursor. """
		if self._x >= self._columns or ch == '\n':
			self._x = 0
			self._y += 1
			if self._y >= self._lines:
				self._y = 0
			self.move_to(self._x, self._y)
		if ch != '\n':
			self._write_data(ord(ch))
			self._x += 1

	def puts(self, s):
		""" Write s to the LCD and advance the cursor. """
		for ch in s:
			self.putch(ch)

	# Private functions

	def _write_byte(self, byte):
		"""	Write byte to LCD and pulse Enable.
			Byte is latched on falling edge of Enable.
		"""
		self._i2c.writeto(self._addr, bytes([byte | self.MASK_EN | self._backlight]))
		self._i2c.writeto(self._addr, bytes([byte | self._backlight]))

	def _write_init_nibble(self, nibble):
		"""	Write upper nibble to the LCD for initialization purposes. """
		self._write_byte(nibble & 0xF0)

	def _write_command(self, cmd):
		"""	Write a command as two nibbles to the LCD. """
		# print("cmd: {0:02X} {0:08b}".format(cmd))
		self._write_byte(cmd & 0xF0)
		self._write_byte((cmd << 4) & 0xF0)
		if cmd <= 3:  # Worst case delay for home and clear commands is 4.1 msec
			sleep_ms(5)

	def _write_data(self, data):
		"""Write data as two nibbles to the LCD. """
		self._write_byte(self.MASK_RS | (data & 0xF0))
		self._write_byte(self.MASK_RS | ((data << 4) & 0xF0))


if __name__ == "__main__":
	"""	Test the LCD functions. """

	# The WiPY 2.0 has one I2C connection (id=0).
	#
	# The PCF8574 in my I2C LCD interface module has I2C address 0x27
	#
	# This address was found by the scan() function from WiPy's I2C library.

	from machine import I2C

	lcd = LCD(I2C(0, I2C.MASTER), addr=39, lines=2, columns=16)

	print("Cursor blink")
	lcd.blink()
	sleep_ms(5000)

	print("Print alfabet")
	for i in range(0, 26):
		lcd.putch(chr(ord('A') + i))
		sleep_ms(100)

	print("Display off")
	lcd.display_off()
	sleep_ms(5000)

	print("Cursor solid")
	lcd.solid()
	sleep_ms(5000)

	print("Display on (cursor now solid)")
	lcd.display_on()
	sleep_ms(5000)

	print("Cursor off")
	lcd.cursor_off()
	sleep_ms(5000)

	print("Cursor on")
	lcd.cursor_on()
	sleep_ms(5000)

	print("Print 0 to 9")
	for i in range(0, 10):
		lcd.putch(chr(ord('0') + i))
	sleep_ms(5000)

	print("Print string HELLO")
	lcd.puts("HELLO")
	sleep_ms(5000)

	print("Backlight off")
	lcd.backlight_off()
	sleep_ms(5000)

	print("Clear and cursor off")
	lcd.clear()
	lcd.cursor_off()

	print("Backlight on")
	lcd.backlight_on()
	sleep_ms(5000)

	print("Print Ready bottom right")
	lcd.move_to(11, 1)
	lcd.puts("Ready")
