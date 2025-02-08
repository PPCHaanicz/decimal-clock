from machine import Pin,SPI,RTC
import time
from settings import SSID, WIFI_PASSWORD

MOSI = 11
SCK = 10    
RCLK = 9

THOUSANDS = 0xFE
HUNDREDS  = 0xFD
TENS      = 0xFB
ONES      = 0xF7
Dot       = 0x80

SEG8Code = [
    0x3F, # 0
    0x06, # 1
    0x5B, # 2
    0x4F, # 3
    0x66, # 4
    0x6D, # 5
    0x7D, # 6
    0x07, # 7
    0x7F, # 8
    0x6F, # 9
    0x77, # A
    0x7C, # b
    0x39, # C
    0x5E, # d
    0x79, # E
    0x71  # F
    ] 
class LED_8SEG():
    def __init__(self):
        self.rclk = Pin(RCLK,Pin.OUT)
        self.rclk(1)
        self.spi = SPI(1)
        self.spi = SPI(1,1000_000)
        self.spi = SPI(1,10000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.SEG8=SEG8Code
    '''
    function: Send Command
    parameter: 
        Num: bit select
        Seg：segment select       
    Info:The data transfer
    '''
    def write_cmd(self, Num, Seg):    
        self.rclk(1)
        self.spi.write(bytearray([Num]))
        self.spi.write(bytearray([Seg]))
        self.rclk(0)
        time.sleep(0.002)
        self.rclk(1)

def sync_time(led):
    """Sync time over NTP"""
    rtc = RTC()
    try:
        import network, ntptime
        wifi = network.WLAN(network.STA_IF)
        wifi.active(True)
        wifi.connect(SSID, WIFI_PASSWORD)
        # time.sleep(5)  # Wait for connection

        display_loading(led, 5)

        if wifi.isconnected():
            ntptime.settime()
            print("Time synced")
            return True
        else:
            return False

    except ImportError:
        print("WARNING: Could not sync device's clock: NTP not available")
        return False

def update_display(led, hours, minutes, dot) -> None:
    """Displays the time on the 7seg display"""
    led.write_cmd(ONES, led.SEG8[minutes % 10])
    led.write_cmd(TENS, led.SEG8[minutes // 10])
    led.write_cmd(HUNDREDS, led.SEG8[hours % 10] | dot)
    led.write_cmd(THOUSANDS, led.SEG8[hours // 10])

def display_error(led) -> None:
    led.write_cmd(ONES, led.SEG8[14])
    led.write_cmd(TENS, led.SEG8[14])
    led.write_cmd(HUNDREDS, led.SEG8[14])
    led.write_cmd(THOUSANDS, led.SEG8[14])

def display_loading(led, duration) -> None:
    SPEED = 6
    cells = [THOUSANDS, HUNDREDS, TENS, ONES]
    
    for i in range(duration * SPEED):
        led.write_cmd(cells[i % 4], 0x80)
        time.sleep(1 / SPEED)

def seconds_since_midnight_cest(cest_time) -> int:
    seconds = cest_time[3] * 3600 + cest_time[4] * 60 + cest_time[5]
    return seconds

def get_cest_time():
    t = time.localtime()  # Get UTC time from RTC

    # Adjust for CEST (UTC+2)
    cest_hour = t[3] + 2
    day = t[2]

    # Handle overflow past 24:00
    if cest_hour >= 24:
        cest_hour -= 24
        day += 1  # Move to next day

    cest_time = (t[0], t[1], day, cest_hour, t[4], t[5], t[6], t[7])
    return cest_time

def main():
    led = LED_8SEG()
    
    if not sync_time(led) :
        while True:
            display_error(led)
            time.sleep(0.001)

    
    while True:
        now = time.time()
        
        # Calculate beginning of next second
        next_tick = now - (now % 1) + 1

        # Get current time, account for timezone as local time isn't local
        SI_seconds = seconds_since_midnight_cest(get_cest_time())
        D_seconds = int(SI_seconds / 0.864)
        hours = D_seconds // 10000
        minutes = D_seconds // 100 % 100
        # print(f"DEBUG\nSI seconds since midnight: {SI_seconds}\nDecimal seconds since midnight: {D_seconds}\nDecimal minutes: {minutes}\nDecimal hours: {hours}\n")
        # Dot is lit up on even seconds
        dot = Dot if (SI_seconds % 2 == 0) else 0

        # Refresh the display until the next second
        while time.time() < next_tick:
            update_display(led, hours, minutes, dot)
            time.sleep(0.001)

if __name__ == '__main__':
    main()