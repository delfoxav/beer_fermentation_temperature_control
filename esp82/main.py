def get_temperature(position):
  ds_sensor.convert_temp()
  time.sleep_ms(750)
  return(str(ds_sensor.read_temp(roms[position])))
 
#Have to define pump speed function 
#def pump_speed()
 
 
while True:
  print("Sending fridge temperature")
  client.publish(topic="fridge_temperature", msg=get_temperature(0))
  time.sleep(1) 
  print("Sending water_temperature") 
  client.publish(topic="water_temperature", msg=get_temperature(0))
  time.sleep(1)
  client.check_msg()

  






