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

def sync_time(ssid, password):
    """Sync time over NTP"""
    rtc = RTC()
    try:
        import network, ntptime
        wifi = network.WLAN(network.STA_IF)
        wifi.active(True)
        wifi.connect(SSID, WIFI_PASSWORD)
        time.sleep(5)  # Wait for connection
        if wifi.isconnected():
            ntptime.settime()
    except ImportError:
        print("WARNING: Could not sync device's clock: NTP not available")

def update_display(led, hours, minutes, dot):
    """Aktualizuje zobrazení LED displeje."""
    led.write_cmd(ONES, led.SEG8[minutes % 10])
    led.write_cmd(TENS, led.SEG8[minutes // 10])
    led.write_cmd(HUNDREDS, led.SEG8[hours % 10] | dot)
    led.write_cmd(THOUSANDS, led.SEG8[hours // 10])

def main():
    # Synchronizuj čas pomocí NTP
    sync_time("ssid", "password")
    TIMEZONE_OFFSET = 1  # Nastav časové pásmo

    led = LED_8SEG()
    
    while True:
        now = time.time()
        # Vypočítej okamžik začátku další sekundy
        next_tick = now - (now % 1) + 1

        # Získej aktuální čas s korekcí časového pásma
        current_time = time.localtime(now)
        hours = (current_time[3] + TIMEZONE_OFFSET) % 24
        minutes = current_time[4]
        seconds = current_time[5]
        # Tečka bliká synchronizovaně se sekundami (bliká, když je sekunda sudá)
        dot = Dot if (seconds % 2 == 0) else 0

        # Obnovuj displej až do začátku další sekundy
        while time.time() < next_tick:
            update_display(led, hours, minutes, dot)
            time.sleep(0.01)  # malá prodleva, aby se CPU nezahltilo

if __name__ == '__main__':
    main()

                            
            
        





