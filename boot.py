import time
import ubinascii
import machine
import micropython
import network
import esp
esp.osdebug(None)
import gc
gc.collect()
import onewire, ds18x20
#really needed?
import urequests
from mqtt import MQTTClient 


#D1
heater =machine.Pin(5, machine.Pin.OUT)


message=""

def sub_cb(topic, msg): 
  #global message 
  message = str(msg.decode("utf-8","ignore")) 
  #print(msg)
  print(message)
  if topic == b'heater_state' and message == 'ON':
    print('Gonna be Hot There!')
    heater.value(1)
    pwm_pump.duty(500)
 
  if topic == b'heater_state' and message == 'OFF':
    print("It's cooling down man!")
    heater.value(0)
    pwm_pump.duty(1023)
 
  if topic == b'pump_speed':
    print('Pump spin set to '+message+" %")
    pwm_pump.duty(int(10.23*float(message)))
  time.sleep(1) 
    
ssid = 'ControlTheRapsberry'
password = 'ControlThePumps'
mqtt_server = '192.168.4.1'


client_id = ubinascii.hexlify(machine.unique_id())


station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)

#just to be sure, I force remove the AP
ap = network.WLAN(network.AP_IF)
ap.active(False)

while station.isconnected() == False:
  pass

print('Connection successful')
print(station.ifconfig())

#define ds18x20 pin D2
ds_pin = machine.Pin(4)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
roms = ds_sensor.scan()

 #all the MQTT_STUFF
def connect_and_subscribe(): 
  global client_id, mqtt_server
  client = MQTTClient(client_id, mqtt_server) 
  client.set_callback(sub_cb) 
  client.connect()
  client.subscribe(topic=b'heater_state') 
  client.subscribe(topic=b'pump_speed') 
  client.publish(topic="ESP82", msg="Hey There Raspberry!")
  return client
  
def restart_and_reconnect():
  print('failed')
  time.sleep(10)
  machine.reset()


try:
  client=connect_and_subscribe()
except OSError as e:
  restart_and_reconnect()
  
#define pump 
#D6
p12 = machine.Pin(12)
pwm_pump=machine.PWM(p12,freq=50)

#D4
pump_pin_1=machine.Pin(2, machine.Pin.OUT)
#D5
pump_pin_2=machine.Pin(14, machine.Pin.OUT)


#set pump direction have to be checked

pump_pin_1.value(0)
pump_pin_2.value(1)
