'''
FILE NAME
   MyApp.py
   Version 0.1

TYPICAL OUTPUT
   A simple web page served by this flask application in the user's browser.
   Presents data from Solar Inverter and DHT22
   - Current values on primary page
     This page contains the current solar output, also temperature and humidity values.

   - Historic data on alternate page
     A second page that displays historical environment data from the SQLite3 database.
     The historical records can be selected by specifying a date range in the request URL.
     The user can now click on one of the date/time buttons to quickly select one of the available record ranges.
     The user can use Jquery widgets to select a date/time range.

END
'''

#from flask import Flask, request, render_template
from flask import Flask
from flask import request
from flask import Markup
from flask import render_template

import logging, sys
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
#logging.basicConfig(filename='PowerCom_Error.log', level=logging.DEBUG)
#logging.debug('/solar')
#logging.info('We processed %d records', len(processed_records))

import time
import datetime
#http://crsmithdev.com/arrow/
import arrow
import sqlite3
import cgi


app = Flask(__name__)
app.debug = True # Make this False if you are no longer debugging


# TEST TEXT FUNCTION
@app.route("/hello", methods=['GET', 'POST'])
def hello():
   return "<html><body><h1 style='color:red'>Welcome to MyApp! I am hosted on a Raspberry Pi !!!</h1></body></html>"


# Serve current data (solar output, also temperature and humidity values) in text format
@app.route("/")
def current():
   import sys

   # TODO rewrite to get latest from the db instead of reading the sensor/s
   # GET current data from DHT22
   #import Adafruit_DHT
   #humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 27)
   temperature, humidity = get_current_temphumd_data()

   # Get Solar data
   solaroutput,solartotal=get_current_solar_data()

   if solaroutput is not None and solartotal is not None and humidity is not None and temperature is not None:
      return render_template("MyApp.html",solaroutput=solaroutput,solartotal=solartotal,temp=temperature,hum=humidity)
   else:
      return render_template("no_data.html")

# get data from the database
# return temperature and humidity from the database
def get_current_temphumd_data():
   import sqlite3
   dbname = '/var/www/lab_app/lab_app.db'
   conn = sqlite3.connect(dbname)
   curs = conn.cursor()
   curs.execute("SELECT temp FROM temperatures WHERE sensorID='1' ORDER by rowid DESC limit 1;")
   rows = curs.fetchall()
   row=rows[-1]
   temperature=float(row[0])

   curs.execute("SELECT temp FROM humidities WHERE sensorID='1' ORDER by rowid DESC limit 1;")
   rows = curs.fetchall()
   row=rows[-1]
   humidity=float(row[0])

#   logging.info('temperature %f', temperature)
#   logging.info('humidity %f', humidity)

   conn.close()
   return temperature, humidity


# get data from the database
# return solaroutput and solartotal from the database
def get_current_solar_data():
   dbname='/home/pi/Desktop/.powercom/powercom.db'
   conn=sqlite3.connect(dbname)
   curs=conn.cursor()
   curs.execute("SELECT ac_power, accumulated_energy FROM readings ORDER by rowid DESC limit 1;")
   rows=curs.fetchall()

   #extract labels and values from table...

   ac_power=0
   accumulated_energy=0

   row=rows[-1]
   ac_power=(row[0])
   accumulated_energy=(row[1])

#   logging.info('rows %s', rows)

   conn.close()
   return ac_power, accumulated_energy






# UNFINSHED CODE BELOW....

# MAIN FUNCTION TO DISPLAY DATA COLLECTED FROM SOLAR INVERTER
#@app.route("/solar", methods=['GET', 'POST'])
# default to show current day
#
@app.route("/solartable")
def main():
   # Show current readings
   # get latest data from the database
   names,records=get_solar_data()

   if len(records) != 0:
      # convert the data into a table
      table=create_solar_day_table(names, records)
      return render_template('MyApp_SolarTable.html', label=names, value=records)
   else:
      return


# get table of Solar data from the database
# return a table of records from the database
def get_solar_data():
   dbname='/home/pi/Desktop/.powercom/powercom.db'
   conn=sqlite3.connect(dbname)
   curs=conn.cursor()

   curs.execute("SELECT reading_datetime, heat_sink_temperature, panel_1_voltage, panel_1_current, working_hours, line_current, line_voltage, ac_frequency, ac_power, accumulated_energy FROM readings ORDER by rowid DESC limit 10;")

   names=list(map(lambda x: x[0], curs.description))
   rows=curs.fetchall()

#   logging.info('row names %s', names)
#   logging.info('rows %s', rows)

   conn.close()
   return names, rows


# convert rows from database into a javascript table
# THIS WORKS
def create_solar_day_table(names, rows):
   mytable=""

   # add column headings
   mytable+="["
   for column in names[:-1]:
      colstr=str(column)
#      logging.info('colstr_label %s', str(column))
      mytable+=colstr + ","
   for column in names[-1]:
      colstr=str(column)
#      logging.info('colstr_label %s', str(column))
      mytable+=colstr
   mytable+="],\n"

   # add data from each row
   for row in rows[:-1]:
      mytable+="["
      for column in row[:-1]:
         colstr=str(column)
#         logging.info('colstr_label %s', str(column))
         mytable+=colstr + ","

      column=row[-1]
      colstr=str(column)
#      logging.info('colstr_label %s', str(column))
      mytable+=colstr
      mytable+="],\n"
#   mytable+="],\n"

   # add data from last row
   row=rows[-1]
   mytable+="["
   for column in row[:-1]:
      colstr=str(column)
#      logging.info('colstr_label %s', str(column))
      mytable+=colstr + ","

   column=row[-1]
   colstr=str(column)
#   logging.info('colstr_label %s', str(column))
   mytable+=colstr
   mytable+="]"

#   logging.info('mytable \n%s', mytable)
   return mytable










@app.route("/lab_env_db", methods=['GET'])  #Add date limits in the URL #Arguments: from=2015-03-04&to=2015-03-05
def lab_env_db():
	temperatures, humidities, timezone, from_date_str, to_date_str = get_records()

	# Create new record tables so that datetimes are adjusted back to the user browser's time zone.
	time_adjusted_temperatures = []
	time_adjusted_humidities   = []
	for record in temperatures:
		local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
		time_adjusted_temperatures.append([local_timedate.format('YYYY-MM-DD HH:mm'), round(record[2],2)])

	for record in humidities:
		local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm").to(timezone)
		time_adjusted_humidities.append([local_timedate.format('YYYY-MM-DD HH:mm'), round(record[2],2)])

	print "rendering lab_env_db.html with: %s, %s, %s" % (timezone, from_date_str, to_date_str)

	return render_template("lab_env_db.html",
				timezone	= timezone,
				temp 		= time_adjusted_temperatures,
				hum 		= time_adjusted_humidities, 
				from_date 	= from_date_str, 
				to_date 	= to_date_str,
				temp_items 	= len(temperatures),
				query_string	= request.query_string, #This query string is used
									#by the Plotly link
				hum_items 	= len(humidities))



def get_records():
	import sqlite3
	from_date_str 	= request.args.get('from',time.strftime("%Y-%m-%d 00:00")) #Get the from date value from the URL
	to_date_str 	= request.args.get('to',time.strftime("%Y-%m-%d %H:%M"))   #Get the to date value from the URL
	timezone 	= request.args.get('timezone','Etc/UTC');
	range_h_form	= request.args.get('range_h','');  #This will return a string, if field range_h exists in the request
	range_h_int 	= "nan"  #initialise this variable with not a number

	print "REQUEST:"
	print request.args
	
	try: 
		range_h_int	= int(range_h_form)
	except:
		range_h_int	= "nan"
	#	print "range_h_form not a number"


	print "1. Received from browser: from: %s, to: %s, timezone: %s, range_h_int %s" % (from_date_str, to_date_str, timezone, range_h_int)
	
	if not validate_date(from_date_str):			# Validate date before sending it to the DB
		from_date_str 	= time.strftime("%Y-%m-%d 00:00")

	if not validate_date(to_date_str):			# Validate date before sending it to the DB
		to_date_str 	= time.strftime("%Y-%m-%d %H:%M")

	#print '2. From: %s, to: %s, timezone: %s' % (from_date_str,to_date_str,timezone)
	# Create datetime object so that we can convert to UTC from the browser's local time
	from_date_obj       = datetime.datetime.strptime(from_date_str,'%Y-%m-%d %H:%M')
	to_date_obj         = datetime.datetime.strptime(to_date_str,'%Y-%m-%d %H:%M')

	# If range_h is defined, we don't need the from and to times
	if isinstance(range_h_int,int):	
		print 'range_h_int: %s' %(range_h_int)

		arrow_time_from = arrow.now().replace(hours=-range_h_int)
		arrow_time_to   = arrow.now()
		print 'arrow_time_from: %s, arrow_time_to: %s' %(arrow_time_from, arrow_time_to)

		from_date_utc   = arrow_time_from.strftime("%Y-%m-%d %H:%M")	
		to_date_utc     = arrow_time_to.strftime("%Y-%m-%d %H:%M")
		print 'from_date_utc: %s, to_date_utc: %s' %(from_date_utc, to_date_utc)

		#from_date_str   = arrow_time_from.to(timezone).strftime("%Y-%m-%d %H:%M")
		#to_date_str     = arrow_time_to.to(timezone).strftime("%Y-%m-%d %H:%M")
		from_date_str   = arrow_time_from.strftime("%Y-%m-%d %H:%M")
		to_date_str     = arrow_time_to.strftime("%Y-%m-%d %H:%M")
		print 'from_date_str: %s, to_date_str: %s' %(from_date_str, to_date_str)

	else:
		#Convert datetimes to UTC so we can retrieve the appropriate records from the database
		from_date_utc   = arrow.get(from_date_obj, timezone).to('Etc/UTC').strftime("%Y-%m-%d %H:%M")	
		to_date_utc     = arrow.get(to_date_obj, timezone).to('Etc/UTC').strftime("%Y-%m-%d %H:%M")
		print 'from_date_utc: %s, to_date_utc: %s' %(from_date_utc, to_date_utc)

	conn 			    = sqlite3.connect('/var/www/lab_app/lab_app.db')
	curs 			    = conn.cursor()
	curs.execute("SELECT * FROM temperatures WHERE sensorID='1' AND rDateTime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
	temperatures 	    = curs.fetchall()
	curs.execute("SELECT * FROM humidities WHERE sensorID='1' AND rDateTime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
	humidities 	    = curs.fetchall()
	conn.close()

	return [temperatures, humidities, timezone, from_date_str, to_date_str]


# FOR REFERENCE ONLY... NOT in use
@app.route("/solar_day")
def main_today():
   # default this to show current day

   # get options that may have been passed to this script
   option=get_option()
   if option is None:
      option = str(24)

    # get data from the database
   records=get_day_data(option)

   if len(records) != 0:
      # convert the data into a table
      #table=create_table(records)

      # display chart
      return make_day_chart(records)
   else:
      return

# get data from the database
# if an interval (str) is passed, 
# return a list of records from the database
def get_day_data(interval):
   dbname='/home/pi/Desktop/.powercom/powercom.db'
   conn=sqlite3.connect(dbname)
   curs=conn.cursor()

#   if interval == None:
      #curs.execute("SELECT * FROM readings")
      #curs.execute("SELECT * FROM daily_summary")
#   else:
      #curs.execute("SELECT reading_datetime, heat_sink_temperature FROM readings WHERE reading_datetime>datetime('now','-%s hours')" % interval)
      #curs.execute("SELECT reading_datetime, ac_power FROM readings WHERE reading_datetime>datetime('now','-%s hours')" % interval)
      #curs.execute("SELECT reading_datetime, ac_power FROM readings WHERE reading_datetime>datetime('time.localtime','-%s hours')" % interval)
      #curs.execute("SELECT reading_date, total_ac_power FROM daily_summary")

   curs.execute("SELECT reading_datetime, ac_power, accumulated_energy FROM readings WHERE substr(reading_datetime, 1, 10) = substr(datetime('now', 'localtime'), 1 ,10)")

   rows=curs.fetchall()
   conn.close()
   return rows

def make_day_chart(rows):
   #extract labels and values from table...

   labels=[]
   values=[]

   for row in rows[:-1]:
      labels.append(str(row[0]))
      values.append(row[1])

   row=rows[-1]
   labels.append(str(row[0]))
   values.append(row[1])

   return render_template('PowerCom_Chart.html', title='Current Day', values=values, labels=labels)


@app.route("/solar_daily")
def main_daily():
   # get options that may have been passed to this script
   option=get_option()
   if option is None:
      option = str(24)

    # get data from the database
   records=get_daily_data(option)

   if len(records) != 0:
      # convert the data into a table
      #table=create_table(records)

      # display chart
      return make_daily_chart(records)
   else:
      return

# get data from the database
# if an interval (str) is passed, 
# return a list of records from the database
def get_daily_data(interval):
   dbname='/home/pi/Desktop/.powercom/powercom.db'
   conn=sqlite3.connect(dbname)
   curs=conn.cursor()

   if interval == None:
      #curs.execute("SELECT * FROM readings")
      curs.execute("SELECT * FROM daily_summary")
   else:
      #curs.execute("SELECT reading_datetime, heat_sink_temperature FROM readings WHERE reading_datetime>datetime('now','-%s hours')" % interval)
      #curs.execute("SELECT reading_datetime, ac_power FROM readings WHERE reading_datetime>datetime('now','-%s hours')" % interval)
      curs.execute("SELECT reading_date, total_ac_power FROM daily_summary")

   rows=curs.fetchall()
   conn.close()
   return rows

def make_daily_chart(rows):
   #extract labels and values from table...

   labels=[]
   values=[]

   for row in rows[:-1]:
      labels.append(str(row[0]))
      values.append(row[1])

   row=rows[-1]
   labels.append(str(row[0]))
   values.append(row[1])

   return render_template('PowerCom_Chart.html', title='Daily', values=values, labels=labels)


## Solar_Month
@app.route("/solar_monthly")
def main_monthly():
   # get options that may have been passed to this script
   option=get_option()
   if option is None:
      option = str(24)

    # get data from the database
   records=get_monthly_data(option)

   if len(records) != 0:
      # convert the data into a table
      #table=create_table(records)

      # display chart
      return make_monthly_chart(records)
   else:
      return

# get data from the database
# if an interval (str) is passed, 
# return a list of records from the database
def get_monthly_data(interval):
   dbname='/home/pi/Desktop/.powercom/powercom.db'
   conn=sqlite3.connect(dbname)
   curs=conn.cursor()

   if interval == None:
      curs.execute("SELECT * FROM monthly_summary")
   else:
      curs.execute("SELECT reading_date, total_ac_power FROM monthly_summary")

   rows=curs.fetchall()
   conn.close()
   return rows

def make_monthly_chart(rows):
   #extract labels and values from table...

   labels=[]
   values=[]

   for row in rows[:-1]:
      labels.append(str(row[0]))
      values.append(row[1])

   row=rows[-1]
   labels.append(str(row[0]))
   values.append(row[1])

   return render_template('PowerCom_Chart.html', title='Monthly', values=values, labels=labels)



### COMMON functions
# check that the option is valid
# and not an SQL injection
def validate_input(option_str):
   # check that the option string represents a number
   if option_str.isalnum():
      # check that the option is within a specific range
      if int(option_str) > 0 and int(option_str) <= 24:
         return option_str
      else:
         return None
   else: 
      return None


#return the option passed to the script
def get_option():
   form=cgi.FieldStorage()
   if "timeinterval" in form:
      option = form["timeinterval"].value
      return validate_input (option)
   else:
      return None








# Test for valid data value
def validate_date(d):
    try:
        datetime.datetime.strptime(d, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False

### UNUSED MISC functions
## convert rows from database into a javascript table
#def create_table(rows):
#   chart_table=""
#
#   for row in rows[:-1]:
#      rowstr="['{0}', {1}],\n".format(str(row[0]),str(row[1]))
##      logging.info('rowstr_label %s', str(row[0]))
##      logging.info('rowstr_value %s', str(row[1]))
#      chart_table+=rowstr
#
#   row=rows[-1]
#   rowstr="['{0}', {1}]\n".format(str(row[0]),str(row[1]))
##   logging.info('rowstr2 %s', rowstr)
#   chart_table+=rowstr
#
#   return chart_table


# Set IP and Port parameters
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
