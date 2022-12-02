import RPi.GPIO as GPIO
import bluetooth_connection
import time

system_started = False
bluetoothManager = bluetooth_connection.BluetoothManagerRB(device_address="00:B8:B6:53:F9:E4")

def start_system():
    if not system_started:
        if bluetoothManager.connect():
            system_started = True
            print("Sistema inicializado...")
            GPIO.output(5,False)
            GPIO.output(6,True)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
#Configuramos el GPIO de entrada
#El led rojo,amarillo y verde de salida

#_____LED_ROJO________
GPIO.setup(17,GPIO.OUT)
GPIO.output(17,True)
time.sleep(10)
GPIO.output(17,False)

#_____LED_AMARILLO________
#GPIO.setup(6,GPIO.OUT)
#GPIO.output(6,False)

#_____LED_VERDE________
#GPIO.setup(26,GPIO.OUT)
#GPIO.output(26,False)

#_________BUTTON___________
#GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#GPIO.add_event_detect(27,GPIO.RISING,callback=start_system)