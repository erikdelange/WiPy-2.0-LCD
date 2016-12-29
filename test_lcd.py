from utime import sleep_ms
from i2c_lcd import LCD


if __name__ == "__main__":
    """ Test all the LCD functions. """

    # The WiPY 2.0 has one I2C connection (id=0).
    # The PCF8574 in my (16x2) I2C LCD interface module has I2C address 0x27
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
    sleep_ms(2000)

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
    sleep_ms(5000)

    print("Move cursor outside display")
    lcd.blink()
    lcd.move_to(100,  100)
