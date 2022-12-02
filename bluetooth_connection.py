import sys
import time
from threading import Thread
from bluetooth import BluetoothSocket, RFCOMM, find_service
from camera import FaceClassification 
from GPIO import GpioManager
from constants import FramesCategory

class BluetoothManagerRB():
    def __init__(self, device_address="C8:3D:DC:80:E9:9F",uuid_service_app="00001101-0000-1000-8000-00805F9B34FB"):
        self.camera_observer = FaceClassification(camera_frame_rate=20, camera_capture_size=[224,224])
        self.camera_observer.initialize_model()
        
        self.gpio_manager = GpioManager()
        
        self.device_address = device_address
        self.uuid_service_app = uuid_service_app
        self.bluetooth_services = []
        self.app_socket = None
        
        self.bluetooth_send_message_thread=None
        self.bluetooth_receive_message_thread=None
        
        self.is_monitoring_active=False
        self.is_connection_enabled=False
        
        self.all_statistics_travel={'ab':int(0), 'av':int(0) ,'st': float(0)}
        self.start_time = float(0)
        self.actual_start_drowsiness_time = float(0)
        self.total_drowsiness_time = float(0)
        
    def send_data_to_device(self):
        print("Empezando monitoreo")
        
        drowsiness_frames = 0
        drowsiness_probability_acc = float(0)
        
        no_drowsiness_frames = 0
        no_drowsiness_probability_acc = float(0)
        
        new_buzzer_activation = True
        new_pwm_activation = True
        
        while self.is_monitoring_active:
            [best,best_prob] = self.camera_observer.predict()
            
            #______________________DECISIONES CON LA PROBABILIDAD OBTENIDA_____________________
            if best == "drowsiness":

                drowsiness_frames += 1
                drowsiness_probability_acc += float(best_prob)

                if drowsiness_frames >= FramesCategory.CONSTANT_DROWSINESS_FRAME_COUNT_LEVEL.value[0]:
                    # Enviamos las estadisticas de somnolencia si lleva 5 o mas frames seguidos
                    self.app_socket.send(f"se:{int(best_prob)}")
                    time.sleep(0.1)
                    
                    no_drowsiness_frames = 0
                    no_drowsiness_probability_acc = float(0)
                    
                    # ____________________________PWM_______________________________
                    if not self.gpio_manager.pwm_status:
                        if not new_pwm_activation:
                            continue
                
                        print("Aumentando en 1 las activaciones del vibrador. Encendiendo pwm")
                        self.gpio_manager.enable_pwm()
                        self.all_statistics_travel['av'] += 1
                        new_pwm_activation = False
                        self.actual_start_drowsiness_time = time.time()
                        continue

                    if drowsiness_frames < FramesCategory.CONSTANT_DROWSINESS_FRAME_COUNT_LEVEL.value[1]:
                        continue

                    if drowsiness_frames == FramesCategory.CONSTANT_DROWSINESS_FRAME_COUNT_LEVEL.value[1]:
                        self.gpio_manager.change_duty_cycle_pwm(2)
                        continue
                    #if drowsiness_frames == FramesCategory.CONSTANT_DROWSINESS_FRAME_COUNT_LEVEL.value[2]:
                        #self.gpio_manager.change_duty_cycle_pwm(3)
                        #continue
                    #if drowsiness_frames == FramesCategory.CONSTANT_DROWSINESS_FRAME_COUNT_LEVEL.value[3]:
                        #self.gpio_manager.change_duty_cycle_pwm(4)
                        #self.app_socket.send(b"sm")
                        #time.sleep(0.1)
                        #print("Solicitdando el envío SMS a los contactos de confianza")
                    # ________________________PWM__________________________________
    
                    # _______________________BUZZER________________________________
                    if not self.gpio_manager.buzzer_status:

                        if drowsiness_frames <= FramesCategory.CONSTANT_DROWSINESS_FRAME_COUNT_LEVEL.value[2]:
                            continue
                        if not new_buzzer_activation:
                            continue
                        
                        self.gpio_manager.change_duty_cycle_pwm(4)
                        self.app_socket.send(b"sm")
                        time.sleep(0.1)
                        print("Solicitdando el envío SMS a los contactos de confianza")
                        
                        print("Aumentando en 1 las activaciones del buzzer. Encendiendo buzzer. DESPIERTA!!!")
                        self.all_statistics_travel['ab'] += 1
                        new_buzzer_activation = False
                        self.gpio_manager.enable_buzzer(
                            float(drowsiness_probability_acc) / float(drowsiness_frames))
                    # _______________________BUZZER_______________________________

            else:

                no_drowsiness_frames += 1
                no_drowsiness_probability_acc += float(best_prob)

                if no_drowsiness_frames >= FramesCategory.CONSTANT_NO_DROWSINESS_FRAME_COUNT.value:

                    drowsiness_frames = 0
                    drowsiness_probability_acc = float(0)

                    if self.gpio_manager.buzzer_status:
                        self.gpio_manager.stop_buzzer(best_prob)
                        new_buzzer_activation = True
                        print("Apagando buzzers")

                    if self.gpio_manager.pwm_status:
                        self.gpio_manager.stop_pwm()
                        new_pwm_activation = True
                        print("Apagando pwm")
                        self.all_statistics_travel['st'] += time.time() - self.actual_start_drowsiness_time
                        self.actual_start_drowsiness_time = float(0)

            print(drowsiness_frames, no_drowsiness_frames)
                    # ______________________DECISIONES CON LA PROBABILIDAD OBTENIDA_____________________
            #if best == "drowsiness":
                
                #drowsiness_frames += 1
                #drowsiness_probability_acc += float(best_prob)
                    
                #if drowsiness_frames >= FramesCategory.CONSTANT_DROWSINESS_FRAME_COUNT_LEVEL.value[1]:
                 #   no_drowsiness_frames = 0
                  #  no_drowsiness_probability_acc = float(0)
                    
                    #____________________________PWM_______________________________
                   # if not self.gpio_manager.pwm_status:
                    #    if new_pwm_activation:
                     #       self.all_statistics_travel['av'] += 1
                      #      new_pwm_activation = False
                       #     print("Aumentando en 1 las activaciones del vibrador")
                        #    self.actual_start_drowsiness_time = time.time()
                        
                        #self.gpio_manager.enable_pwm()
                        #print("Encendiendo pwm")
                        #continue
                
                    #if self.gpio_manager.pwm_status:
                        
                     #   if drowsiness_frames < 10:
                      #      continue
                        
                       # if drowsiness_frames == 10:
                        #    self.gpio_manager.change_duty_cycle_pwm(2)
                        #if drowsiness_frames == 15:
                         #   self.gpio_manager.change_duty_cycle_pwm(3)
                        #if drowsiness_frames == 19:
                        #    self.gpio_manager.change_duty_cycle_pwm(4)
                    #________________________PWM__________________________________
                    
                    #_______________________BUZZER________________________________
                    #if not self.gpio_manager.buzzer_status:
                    
                     #   if drowsiness_frames > 20:
                        
                      #      if new_buzzer_activation:
                       #         self.all_statistics_travel['ab'] += 1
                        #        new_buzzer_activation = False
                         #       print("Aumentando en 1 las activaciones del buzzer")
                                
                          #  self.gpio_manager.enable_buzzer(float(drowsiness_probability_acc) / float(drowsiness_frames))
                           # print("Encendiendo buzzer. DESPIERTA!!!")
                     #_______________________BUZZER_______________________________
                            
                    #Enviamos las estadisticas del frame actual
                    #self.app_socket.send(f"se:{best_prob:.2f}")
            #else:
                
            #    no_drowsiness_frames += 1
             #   no_drowsiness_probability_acc += float(best_prob)
                
              #  if no_drowsiness_frames >= 5:
               #     drowsiness_frames = 0
                #    drowsiness_probability_acc = float(0)
                    
                 #   if self.gpio_manager.buzzer_status:
                  #      self.gpio_manager.stop_buzzer(best_prob)
                   #     new_buzzer_activation = True
                    #    print("Apagando buzzers")
                    
           #         if self.gpio_manager.pwm_status:
            #            self.gpio_manager.stop_pwm()
             #           new_pwm_activation = True
              #          print("Apagando pwm")                    
               #         self.all_statistics_travel['st'] += time.time() - self.actual_start_drowsiness_time
                #        self.actual_start_drowsiness_time = float(0)
                        
            #print(drowsiness_frames,no_drowsiness_frames)
            
    def receive_data_from_device(self):
        while self.is_connection_enabled:
            try:
                #Esperamos el mensaje para iniciar/finalizar el sistema
                bytesMessRecv = self.app_socket.recv(1024)
                
                #Verificamos que hayamos recibido el mensaje correctamente
                if len(bytesMessRecv) == 0:
                    print("Error al recibir mensaje")
                    continue
                
                if  bytesMessRecv == b"FIN":
                    print("Apagando los sistemas")
                    self.stop_monitoring()#Apagamos el sistema
                
                if bytesMessRecv == b"DATA-OK":
                    print("Datos enviados correctamente")
                    self.is_connection_enabled = False
                    self.is_monitoring_active = False
                    break
            except:
                print("Espera alcanzada...")
        print("se acabó")
        self.gpio_manager.stop_led()
        self.connect()
                 
    def search_service(self):
        self.gpio_manager.enable_led("YELLOW")
        self.bluetooth_services = []
        while len(self.bluetooth_services) < 1:
            print("Buscando servicios...")
            self.bluetooth_services = find_service(address = self.device_address , uuid = self.uuid_service_app)
            
            if len(self.bluetooth_services) < 1:
                time.sleep(5)
            
    def connect(self):
        #Creamos un hilo para continuamente buscar el servicio
        #hasta encontrarlo, es decir, hasta que inicie un nuevo recorrido
        search_service_thread = Thread(target=self.search_service,name="ss")
        search_service_thread.start()
        search_service_thread.join()
        
        if self.gpio_manager.led_status:
            self.gpio_manager.stop_led()
        
        #Si no lo encontramos, finalizamos
        if len(self.bluetooth_services) == 0:
            return False
        
        app_service_data = self.bluetooth_services[0]
        
        print("Servicio encontrado. Conectandose...")

        self.app_socket = BluetoothSocket(RFCOMM)
                
        try:
            self.app_socket.connect((self.device_address, app_service_data['port']))
            self.gpio_manager.enable_led("GREEN")
            self.is_connection_enabled = True
            self.start_monitoring()
        except KeyboardInterrupt:
            return False
        except:
            return False
        
        return True
    
    def start_monitoring(self):
        self.start_time = time.time()
        self.is_monitoring_active = True
        
        self.bluetooth_send_message_thread = Thread(target = self.send_data_to_device, name="bt")
        self.bluetooth_receive_message_thread = Thread(target = self.receive_data_from_device, name="btrecv")
        
        self.bluetooth_receive_message_thread.start()
        self.bluetooth_send_message_thread.start()
        
    def stop_monitoring(self):
        self.is_monitoring_active = False
        
        self.bluetooth_send_message_thread.join()
        
        #Apagamos los buzzers y pwm si es que se quedaron activos
        if self.gpio_manager.buzzer_status:
            self.gpio_manager.stop_buzzer()
        
        if self.gpio_manager.pwm_status:
            self.gpio_manager.stop_pwm()
            
        #Obtenemos el tiempo total del recorrido
        time_of_travel = time.time() - self.start_time
        
        #Si finaliza el sistema antes de que cambie su estado de drowsiness a normal, nos aseguramos de acumular ese tiempo
        if not self.actual_start_drowsiness_time == float(0):
            self.all_statistics_travel['st'] += time.time() - self.actual_start_drowsiness_time
        
        #Enviamos los datos a la aplicacion
        time_travel_join = "tt:"+ str(int(time_of_travel))
        time_travel_encoded = bytes(time_travel_join,'utf-8')

        active_buzzers_join = "ab:" + str(self.all_statistics_travel['ab'])
        active_buzzers_encoded = bytes(active_buzzers_join,'utf-8')

        active_pwm_join = "av:" + str(self.all_statistics_travel['av'])
        active_pwm_encoded = bytes(active_pwm_join,'utf-8')

        sleepy_time_join = "st:" + str(int(self.all_statistics_travel['st']))
        sleepy_time_encoded = bytes(sleepy_time_join,'utf-8')
        
        print(time_travel_encoded)
        print(active_buzzers_encoded)
        print(active_pwm_encoded)
        print(sleepy_time_encoded)
        
        self.app_socket.send(time_travel_encoded)
        time.sleep(0.5)
        self.app_socket.send(b'')
        self.app_socket.send(active_buzzers_encoded)
        time.sleep(0.5)
        self.app_socket.send(b'')
        self.app_socket.send(active_pwm_encoded)
        time.sleep(0.5)
        self.app_socket.send(b'')
        self.app_socket.send(sleepy_time_encoded)
        time.sleep(0.5)
        
    def get_bluetooth_socket(self):
        return self.app_socket
    
    def get_device_mac_address(self):
        return self.device_address
    
    def is_connection_active(self):
        return self.is_connection_enabled
    
    def is_monitoring(self):
        return self.is_monitoring_active