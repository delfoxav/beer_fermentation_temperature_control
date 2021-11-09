# beer_fermentation_temperature_control
Control the temperature of a beer bioreactor and keep it to a defined setpoint.

Upload all the ESP82 code to an ESP82 running micropython. The code should be adapted in order to connect to the right AP or wifi with the right IP address


The raspberry part should be uploaded on a rpi running debian (desktop version is recommanded) and running his own access point. 

The templates of the graphs can be changed


TODO:

-implement a real control algorithm
- check if the messages are get/send
- send some "control" message at random time
- enhance the graphs
- store the data in a real database
