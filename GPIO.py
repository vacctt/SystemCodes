import RPi.GPIO as GPIO
import time
from threading import Thread
import math
import sys
from constants import PwmLevels

class GpioManager():
    def __init__(self, pin_out_buzzer=26, pin_out_pwm=12, pin_out_green=23, pin_out_yellow=25, pwm_frequency=1, pwm_duty_cycle=16, duty_cicle_base=16, duty_cycle_factor=28):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_out_buzzer, GPIO.OUT)
        GPIO.setup(pin_out_pwm, GPIO.OUT)
        GPIO.setup(pin_out_green,GPIO.OUT)
        GPIO.setup(pin_out_yellow,GPIO.OUT)
        
        GPIO.output(pin_out_pwm,False)
        GPIO.output(pin_out_green,False)
        GPIO.output(pin_out_yellow,False)
        GPIO.output(pin_out_buzzer,False)
        
        self.buzzer_status = False
        self.pwm_status = False
        self.led_status = False
        self.led_on = ""
        
        self.pin_out_buzzer = pin_out_buzzer
        self.pin_out_pwm = pin_out_pwm
        self.pin_out_green_led = pin_out_green
        self.pin_out_yellow_led = pin_out_yellow
        
        self.buzzer_on_thread = None
        self.pwm_on_thread = None
        self.led_on_thread = None
        
        self.pwm_pin = GPIO.PWM(self.pin_out_pwm, pwm_frequency)
        self.duty_cycle = pwm_duty_cycle
        self.duty_cicle_base = duty_cicle_base
        self.duty_cicle_factor = duty_cycle_factor
    
    def start_led_thread(self, led):
        print("Led thread iniciado\n")
        
        self.led_on = led
        if led == "GREEN":
            GPIO.output(self.pin_out_green_led, True)
        if led == "YELLOW":
            GPIO.output(self.pin_out_yellow_led, True)
            
        while self.led_status:
            continue
        
        print(f"Led {led} apagado")     
        
    def enable_led(self, led_to_enable=""):
        if not led_to_enable == "":
            self.led_status = True
            self.led_on_thread = Thread(target=self.start_led_thread,kwargs={'led':led_to_enable} ,name="lot")
            print("Solicitud para encender led iniciada")
            self.led_on_thread.start()
    
    def stop_led(self):
        print("Apagando Led")
        self.led_status = False#Cambiamos la bandera del ciclo del hilo que tiene la activacion del buzzer
        
        if self.led_on == "GREEN":
            GPIO.output(self.pin_out_green_led, False)
        if self.led_on == "YELLOW":
            GPIO.output(self.pin_out_yellow_led, False)
        
        self.led_on_thread.join()#Esperamos a que se termine el ciclo del hilo
        
    def start_buzzer_thread(self, prob_drowsiness):
        
        drowsiness_level = math.floor( prob_drowsiness/float(10) ) - 4
        frequency_buzzer = float(1) - ( ( drowsiness_level  - float(1) )  * 0.2)
        
        print("Buzzer thread iniciado")
        
        while self.buzzer_status:
            GPIO.output(self.pin_out_buzzer, True)
            time.sleep(frequency_buzzer)
            GPIO.output(self.pin_out_buzzer, False)
            time.sleep(frequency_buzzer)
            
        print("Buzzer thread finalizado")
    
    def enable_buzzer(self,prob_drowsiness):
        self.buzzer_status = True
        self.buzzer_on_thread = Thread(target = self.start_buzzer_thread,kwargs={'prob_drowsiness':prob_drowsiness},name="bzz")
        self.buzzer_on_thread.start()
        print("Solicitud para encender buzzers iniciada")

    def stop_buzzer(self,prob_drowsiness):
        print("Apagando buzzers")
        self.buzzer_status = False#Cambiamos la bandera del ciclo del hilo que tiene la activacion del buzzer
        self.buzzer_on_thread.join()#Esperamos a que se termine el ciclo del hilo
    
    def start_pwm_thread(self):
        #Inicializamos la salida de pwm
        self.pwm_pin.start(self.duty_cycle)
        
        print("PWM  thread iniciado")
        
        #Mientras no se haya recibido la solicitud para detener el pwm, continuamos
        while self.pwm_status:
            continue
        
        #Detenemos la salida de pwm
        self.pwm_pin.stop()
        print("PWM thread finalizado")
        
    def enable_pwm(self):
        self.pwm_status = True
        self.pwm_on_thread = Thread(target = self.start_pwm_thread,name = "pwmv")
        print("Solicitud para encender pwm iniciada")
        self.pwm_on_thread.start()
    
    def change_duty_cycle_pwm(self, nvl):
        
        #Nos aseguramos que siempre el nivel mas alto sea 4
        if nvl > PwmLevels.MAX_LEVEL_PWM.value:
            nvl = PwmLevels.MAX_LEVEL_PWM.value
            
        #Cambiamos el ciclo de trabajo del pwm dependiendo el nivel
        new_pwm_duty_cycle = self.duty_cicle_base  + ( self.duty_cicle_factor * (int(nvl) - 1) )
        
        #Nos aseguramos que nunca sobre pase el limite de 100
        if new_pwm_duty_cycle > PwmLevels.MAX_DUTY_CYCLE_PWM.value:
            new_pwm_duty_cycle = PwmLevels.MAX_DUTY_CYCLE_PWM.value
        
        self.pwm_pin.ChangeDutyCycle( new_pwm_duty_cycle )
        
        print(f"El ciclo de trabajo del pwm se ha modificado a {new_pwm_duty_cycle}")
        
    def stop_pwm(self):
        print("Pwm terminado")
        self.pwm_status = False