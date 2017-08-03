#!/usr/bin/env python

'''
FILE NAME
env_log.py

1. WHAT IT DOES
Takes a reading from a DHT sensor and
records the values in an SQLite3 database using a Raspberry Pi.

2. REQUIRES
* Any Raspberry Pi
* A DHT sensor
* A 10kOhm resistor
* Jumper wires

3. ORIGINAL WORK
Raspberry Full stack 2015, Peter Dalmaris

4. HARDWARE
   OUTSIDE - sensorID=2
      D17: Power pin for sensor
      D27: Data pin for sensor
   SHED - sensorID=1
      D3: Power pin for sensor
      D4: Data pin for sensor

5. SOFTWARE
Command line terminal
Simple text editor
Libraries:
  import sqlite3
  import sys
  import Adafruit_DHT

6. WARNING!
None

7. CREATED

8. TYPICAL OUTPUT
No text output.
Two new records are inserted in the database when the script is executed
    1 for Temp
    2 for Humidity

9. COMMENTS

10. END
'''


import sqlite3
import Adafruit_DHT
import time
import RPi.GPIO as GPIO


# Function to store data from Sensor in to database
def log_values(sensor_id, temp, hum):
    conn = sqlite3.connect('/var/www/lab_app/lab_app.db')
    # It is important to provide an absolute path to the database
    # file, otherwise Cron won't be able to find it!
    curs = conn.cursor()
    curs.execute("""INSERT INTO temperatures values(datetime(CURRENT_TIMESTAMP, 'localtime') ,(?), round((?), 2))""", (sensor_id, temp))
    curs.execute("""INSERT INTO humidities values(datetime(CURRENT_TIMESTAMP, 'localtime'), (?), round((?), 2))""", (sensor_id, hum))
    conn.commit()
    conn.close()


# Function to get data from the database
# return average of 'n' values for temperature and humidity from the database
def get_average_temphumd_data(n):
    conn = sqlite3.connect('/var/www/lab_app/lab_app.db')
    curs = conn.cursor()

    #print "n=", n
    if n == None:
        n = 3

    #curs.execute("SELECT ROUND(avg(dt.temp),2) FROM (SELECT temp FROM temperatures WHERE sensorID='1' ORDER by rowid DESC limit 3) dt;")
    curs.execute("SELECT ROUND(avg(dt.temp),2) FROM (SELECT temp FROM temperatures WHERE sensorID='1' ORDER by rowid DESC limit %s) dt;" % n)
    rows = curs.fetchall()
    row=rows[-1]
    avg_temp=float(row[0])

    #curs.execute("SELECT ROUND(avg(dt.temp),2) FROM (SELECT temp FROM humidities WHERE sensorID='1' ORDER by rowid DESC limit 3) dt;")
    curs.execute("SELECT ROUND(avg(dt.temp),2) FROM (SELECT temp FROM humidities WHERE sensorID='1' ORDER by rowid DESC limit %s) dt;" % n)
    rows = curs.fetchall()
    row=rows[-1]
    avg_humd=float(row[0])

    #print "avg temp ", (avg_temp)
    #print "avg humd ", (avg_humd)

    conn.close()
    return avg_humd, avg_temp


# Function to check change between current and previous values
# def get_change(current, previous):
#     if current == previous
#         return 100.0
#     try:
#        return (abs(current - previous))/previous)*100.0
#     except ZeroDivisionError:
#         return 0


## MAIN FUNCTION ######################################
#DHT22 Sensor Connections
Sensor = Adafruit_DHT.AM2302
Sensor_Power = 3
Sensor_Data = 4

# Set GPIO mode and set Output high to power Sensor
GPIO.setmode(GPIO.BCM)
GPIO.setup(Sensor_Power, GPIO.OUT)
GPIO.output(Sensor_Power, GPIO.HIGH)

#Get initial readings from the DHT Sensor
#Do While type loop for 'loopcount' cycles
loopcount = 3
bReading = False
while True:
    #Get initial readings from the DHT Sensor
    #print "Get Readings"
    humidity, temperature = Adafruit_DHT.read_retry(Sensor, Sensor_Data)

    # If you don't have a sensor but still wish to run this program, comment
    # out all the sensor related lines, and uncomment the following lines
    # (these will produce random numbers for the temperature and humidity variables)
    #     import random
    #     humidity = random.randint(1,100)
    #     temperature = random.randint(10,30)

    #print "temperature = ", temperature
    #print "humidity = ", humidity
    #print "Got Reading..."

    loopcount -=1
    #print "loopcount = ", loopcount

    # if no reading within the loop count the failout...
    if loopcount <= 0:
        bReading = False
        #print "Break - Loopcount Exceeded!!"
        break

    # occasionally the sensor stops responding
    # toggle the power pin as attempt to restart the sensor
    elif humidity is None or temperature is None:
        #print "PowerCycling Sensor!!"
        GPIO.output(Sensor_Power, GPIO.LOW)  # sensor off
        time.sleep(10)	# wait 10 sec
        GPIO.output(Sensor_Power, GPIO.HIGH)  # sensor on
        time.sleep(5)	# wait 5 sec for sensor to power up

    elif (humidity is not None and temperature is not None):
        bReading = True
        ## TEMP to addres issue where data points lost and average isnt useful...
        ##log_values("1", temperature, humidity)
        
        #occasional error with data values; check within reasonable range of previous values
        #Get average for temperature and humidity from database
        if bReading == True:
            RowsForAvg = 4
            avg_humidity, avg_temperature = get_average_temphumd_data(RowsForAvg)
            #print "avg temp ", (avg_temperature)
            #print "avg humd ", (avg_humidity)
        
        
        # compare readings to respective averages; with tolerance
        bTempAvg = False
        bHumdAvg = False
        #tolerance =0.05 		# e.g. 5%
        tolerance = 0.10 		# e.g. 10%
        toleranceHigh = 1 + tolerance	# e.g. 1.05
        toleranceLow  = 1 - tolerance	# e.g. 0.95%
        #print "tolerance = ", tolerance

        #check temperature
        #print "temperature average low = ", (avg_temperature * toleranceLow)
        #print "temperature average high = ", (avg_temperature * toleranceHigh)
        if temperature < (avg_temperature * toleranceLow):
            #print "temp BELOW average band ", temperature, avg_temperature
            bTempAvg = False
        elif temperature > (avg_temperature * toleranceHigh):
            #print "temp ABOVE average band ", temperature, avg_temperature
            bTempAvg = False
        else:
            #print "temp within average band ", temperature, avg_temperature
            bTempAvg = True

        #check humidity
        #print "humidity average low = ", (avg_humidity * toleranceLow)
        #print "humidity average high = ", (avg_humidity * toleranceHigh)
        if humidity < (avg_humidity * toleranceLow):
            #print "humd BELOW average band ", humidity, avg_humidity
            bHumdAvg = False
        elif humidity > (avg_humidity * toleranceHigh):
            #print "humd ABOVE average band ", humidity, avg_humidity
            bHumdAvg = False
        else:
            #print "humd within average band ", humidity, avg_humidity
            bHumdAvg = True

        #bTempAvg = True
        #bHumdAvg = True
        if bTempAvg == True and bHumdAvg == True:
            #print "Break - Got Readings :)"
            #temperature = temperature * 9/5.0 + 32	# used to convert to Farneheit
            log_values("1", temperature, humidity)
            break
        #else:
            #print "Break - NO Readings :("
            #log_values("1", -999, -999)

    else:
        time.sleep(5)      # short wait to prevent reading sensor too frequently

GPIO.cleanup()

## END MAIN FUNCTOIN
