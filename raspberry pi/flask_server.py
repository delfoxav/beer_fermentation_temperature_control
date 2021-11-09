from flask import Flask, jsonify, render_template, request 
from flask_cors import CORS 
from datetime import datetime #from w1thermsensor import W1ThermSensor 
from random import seed 
from random import uniform 
from get_data import get_data 
import sys 
import logging 
from flask_mqtt import Mqtt 
from multiprocessing import Process, Value 
import time 
import paho.mqtt.client as mqtt_paho 
import threading 
import sys 
import csv 
import os.path

filename="data.csv"

#Check if  *csv exist if not create it with headers
if not os.path.isfile(filename):
	file = open("data.csv","w")
	writer = csv.writer(file)
	header = ["datatime","fermenter_temperature","cooler_temperature","gravity","heater","pump"]
	writer.writerow(header)
	file.close()


#from read_serial import read_serial
seed(1)
start_time=datetime.now()

app = Flask(__name__,
static_folder='static',
template_folder='templates')
CORS(app)
app.config['MQTT_BROKER_URL'] = '192.168.4.1'  # use the free broker from HIVEMQ
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_USERNAME'] = ''  # set the username here if you need authentication for the broker
app.config['MQTT_CLIENT_ID']='flask_get_data' 
app.config['MQTT_PASSWORD'] = ''  # set the password here if the broker demands authentication
app.config['MQTT_KEEPALIVE'] = 5  # set the time interval for sending a ping to the broker to 5 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

##############On initialise le client Mqtt pour flask qui va recevoir les data########################
mqtt = Mqtt(app)

@mqtt.on_connect()
def handle_connect(client,userdata,flags,rc):
	mqtt.subscribe('water_temperature')
	mqtt.subscribe('fridge_temperature')
	mqtt.subscribe('pump_speed')
	mqtt.subscribe('heater_state')
	mqtt.subscribe('ispindel/iSpindel000/temperature')
	mqtt.subscribe('ispindel/iSpindel000/tilt')
	mqtt.subscribe('ispindel/iSpindel000/battery')
	mqtt.subscribe('ispindel/iSpindel000/gravity')
	print("CONNECTED")

paho_client=mqtt_paho.Client()
paho_client.connect("192.168.4.1",1883,60)
	
############Compare flot function######################
def isequal(x,y):
	larger=max(abs(x),abs(y))
	return abs(x-y)<=larger*sys.float_info.epsilon

########On defini nos valeurs limites de temperature a changer avec des requests btw###############
max_temperature=22
min_temperature=18
actual_temperature=20.0


#######On initialise la temperature du fermenteur pour pouvoir la changer apres sans soucis et avoir qqch a tester######
data={'fermenter_temperature':30,'max_temperature':max_temperature,'min_temperature':min_temperature,'water_temperature':0,'fermenter_gravity':0,'pump_speed':0,'heater_state':0}
###On def les routes etc..

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
	print("got message")
	global data
	global start_time
	print(datetime.now()-start_time)
	data['timestamp']=datetime.now().__str__()
	if (message.topic == "heater_state"):
		data[message.topic]=message.payload.decode()
	elif(message.topic == 'ispindel/iSpindel000/temperature'):
		data['fermenter_temperature']=float(message.payload.decode())
	elif(message.topic == 'ispindel/iSpindel000/gravity'):
		data['fermenter_gravity']=float(message.payload.decode())
	elif(message.topic == 'ispindel/iSpindel000/battery'):
		data['fermenter_battery']=float(message.payload.decode())
	elif(message.topic == 'ispindel/iSpindel000/tilt'):
		data['fermenter_tilt']=float(message.payload.decode())
	else:
		data[message.topic]=float(message.payload.decode())
	if((datetime.now()-start_time).seconds>900):
		 start_time=datetime.now()
		 file =open(filename,'a')
		 writer =csv.writer(file)
		 writer.writerow([data['timestamp'],data['fermenter_temperature'],data['water_temperature'],data['fermenter_gravity'],data['heater_state'],data['pump_speed']])
		 print("SAVING")

@app.route('/fridge')
def fridge():
    return render_template("fridge_temperature_stream.html")

@app.route('/water')
def water():
	return render_template("water_temperature_stream.html")

@app.route('/pump')
def pump():
	return render_template("pump_speed_stream.html")

@app.route('/fermenter')
def fermenter():
	return render_template("fermenter_temperature_stream.html")


@app.route('/gravity')
def gravity():
	return render_template("fermenter_density_stream.html")

@app.route('/battery_Ispindel')
def battery_Ispindel():
	return render_template("Ispindel_battery_stream.html")


@app.route('/mqtt')
def mqtt():
	return jsonify(data)

@app.route('/control') 
def parse_request(): 
	global max_temperature
	global min_temperature
	data['max_temperature'] = float(request.args['max_temperature'])
	data['min_temperature'] = float(request.args['min_temperature'])
	return(render_template('temperature_set_point.html',max_temperature=max_temperature,min_temperature=min_temperature))
	

def control():
	global actual_temperature
	while True:
			if (data['fermenter_temperature']>=data['max_temperature']) and (not isequal(data['fermenter_temperature'],actual_temperature)):
				#print("COOL DOWN")
				paho_client.publish("heater_state","OFF")
				paho_client.publish('pump_speed','100')
				actual_temperature=data['fermenter_temperature']
			if (data['fermenter_temperature']<=data['min_temperature']) and (not isequal(data['fermenter_temperature'],actual_temperature)):
				#print("HEATING UP")
				paho_client.publish("heater_state","ON")
				paho_client.publish('pump_speed','10')
				actual_temperature=data['fermenter_temperature']
			if(not isequal(data['max_temperature'],max_temperature)) or (not isequal(data['min_temperature'],min_temperature)):
				actual_temperature=0
			time.sleep(2)


if __name__=="__main__":
	kwargs={'host':'0.0.0.0','threaded':True,'use_reloader':False,'debug':False}
	
	controlThread=threading.Thread(target=control,args=()).start()
	flaskThread=threading.Thread(target=app.run,kwargs=kwargs).start()
	
#if __name__ == "__main__":
#	recording_on=Value('b',True)
#	p=Process(target=record_loop,args=(recording_on,))
#	p.start()
#	app.run(host='0.0.0.0',debug=True,use_reloader=False)
#	p.join()
