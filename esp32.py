# This code will be executed when esp32 is turn on

from mfrc522 import MFRC522
from machine import Pin, SPI
import network
import urequests
import time

# WiFi credentials - Add your own credentials
SSID = ""
PASSWORD = ""

# Server details - Update with your Raspberry Pi's IP address
SERVER_URL = "https://192.168.1.102/api/esp32_rfid" 

class RFIDReader:
    def __init__(self):
        self.spi = SPI(2, baudrate=2500000, polarity=0, phase=0)
        self.spi.init()
        self.rdr = MFRC522(spi=self.spi, gpioRst=4, gpioCs=5)
        self.last_read_id = None
        self.last_read_time = 0
        self.READ_DELAY = 3

    def calculate_id(self, raw_uid):
        # Converter bytes para decimal de forma reversa
        uid_decimal = 0
        for byte in reversed(raw_uid):
            uid_decimal = (uid_decimal << 8) | byte
        return str(uid_decimal)

    def read_card(self):
        try:
            (stat, tag_type) = self.rdr.request(self.rdr.REQIDL)
            
            if stat == self.rdr.OK:
                (stat, raw_uid) = self.rdr.anticoll()
                if stat == self.rdr.OK:
                    # Usar apenas o cálculo original
                    card_id = (raw_uid[0] << 32) | (raw_uid[1] << 24) | (raw_uid[2] << 16) | (raw_uid[3] << 8) | raw_uid[4]
                    
                    current_time = time.time()
                    if (str(card_id) != self.last_read_id or 
                        current_time - self.last_read_time >= self.READ_DELAY):
                        
                        self.last_read_id = str(card_id)
                        self.last_read_time = current_time
                        return str(card_id)
        except Exception as e:
            print('Error reading card:', str(e))
        return None

    def connect_wifi(self):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print('Connecting to WiFi...')
            wlan.connect(SSID, PASSWORD)
            while not wlan.isconnected():
                time.sleep(1)
        print('WiFi connected:', wlan.ifconfig())
        print(f'Make sure your Flask server is running and accessible at: {SERVER_URL}')

    def send_to_server(self, card_id):
        try:
            # Converter para inteiro e depois string para garantir formato correto
            card_id_int = int(card_id)
            data = {'rfid_id': str(card_id_int)}
            
            print(f'Sending to server: {SERVER_URL}')
            print(f'Data: {data}')
            
            headers = {
                'content-type': 'application/json',
                'accept': 'application/json'
            }
            
            response = urequests.post(
                SERVER_URL,
                json=data,
                headers=headers
            )
            
            print('Response status:', response.status_code)
            print('Response text:', response.text)
            response.close()
            return True
            
        except Exception as e:
            print('Error sending to server:', str(e))
            return False

    def test_server_connection(self):
        try:
            response = urequests.get(SERVER_URL)
            print('Server test response status:', response.status_code)
            response.close()
            return True
        except Exception as e:
            print('Server test failed:', str(e))
            return False

    def run(self):
        print('Testing server connection...')
        if not self.test_server_connection():
            print('Unable to connect to server. Please check the server URL and ensure it is running.')
            return
            
        print('Place card near the reader...')
        while True:
            try:
                card_id = self.read_card()
                if card_id:
                    print('Card detected, UID:', card_id)
                    if self.send_to_server(card_id):
                        print('Successfully sent to server')
                    else:
                        print('Failed to send to server')
                time.sleep(0.1)
                
            except Exception as e:
                print('Error in main loop:', str(e))
                time.sleep(1)

def main():
    reader = RFIDReader()
    reader.connect_wifi()
    reader.run()

if __name__ == '__main__':
    main()
