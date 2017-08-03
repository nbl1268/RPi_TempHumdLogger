Raspberry Pi
Logging temperature and humditiy from a DHT22 sensor and presented via webpage


Data collection
	env_log_shed.py

	executed each minute using crontab
	queries DHT22 sensor for readings and stores them in SQLITE3 db



Webpage provides
- Current readings (from sensor)
- Historical values from database


Usage
IP:5002
	for home page showing current readings


IP:5002/hello
	for test page


IP:5002/solartable
	for a table of latest 10 readings from the solar inverter readings database


IP:5002/lab_env_db
	for a table and chart for temperature and humidity readings from the database




