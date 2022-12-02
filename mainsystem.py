import bluetooth_connection

class MainSystem():
    def __init__(self):
        self.bluetoothManager = bluetooth_connection.BluetoothManagerRB(device_address="00:B8:B6:53:F9:E4")
        
    def start(self):
        print("Sistema iniciado")
        if not self.bluetoothManager.connect():
            raise(":(")
    
if __name__ == "__main__":
    
    main = MainSystem()
    main.start()