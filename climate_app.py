# Import Dependencies
import pandas as pd 
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import datetime as dt

from flask import Flask, jsonify

# Create the connection engine
engine = create_engine("sqlite:///hawaii.sqlite")
conn = engine.connect()

# Use SQLAlchemy `automap_base()` to reflect your tables into classes
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save a reference to those classes called `Station` and `Measurement`
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session for the engine to manipulate data
session = Session(engine)

# Set up flask app
app = Flask(__name__)

# Create API welcome page
@app.route("/api/v1.0/")
def welcome():
	"""Returns a welcome page with available API routes"""
	return "<center><h2><b>~~~~~~Aloha! Surf's up!(◕▿◕✿)~~~~~~ </b></h2><br/>\
	<img src='https://media3.giphy.com/media/3oKIPprajCN0pYyhvG/giphy.gif'><br/>\
	Planning your next trip to beautiful sun-kissed Hawaii? <br/>\
    Check out her rainfall and weather with our Hawaii API.<br/>\
    Just copy and paste the routes into the browser after 127.0.0.1:5000<p>\
	<h3>Available Routes: </h3> <br/>\
	Weather Stations | /api/v1.0/stations <br/>\
	Precipitation | /api/v1.0/precipitation <br/>\
	Temperature Observations | /api/v1.0/tobs<br/>\
	Daily Normals (desired date) | /api/v1.0/YYYY-MM-DD<br/>\
	Daily Normals (desired start date and end date) | /api/v1.0/YYYY-MM-DD/YYYY-MM-DD</center>"

# Flask route for precipitation analysis
@app.route("/api/v1.0/precipitation")
def precipitation():
	"""Returns a json list of stations, precipitation, and dates"""
	# Find most recent date of records
	date_query = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
	date_query_results = list(np.ravel(date_query))
	date_split = date_query_results[0].split('-')
	current_year = dt.date(int(date_split[0]), int(date_split[1]), int(date_split[2]))

	# Design a query to retrieve the last 12 months of precipitation data.
	last_year = current_year - dt.timedelta(days=365)
	prcp_query = session.query(Measurement.station,Measurement.date, Measurement.prcp).\
							filter(Measurement.date > last_year).order_by(Measurement.date)
	
	# Convert the query results to a Dictionary using `date` as the key and `tobs` as the value
	prcp_data = []
	for prcp in prcp_query:
		prcp_dict = {}
		prcp_dict["Station"] = prcp.station
		prcp_dict[prcp.date] = prcp.prcp
		prcp_data.append(prcp_dict)
	
	# Return the json representation of your dictionary
	return jsonify(prcp_data)

# Flask route for stations list
@app.route("/api/v1.0/stations")
def stations():
	"""Returns a json list of stations and their names"""
	# Design a query to calculate the total number of stations.
	stations_query = session.query(Station.station, Station.name).all()
	
	# Convert query results to a Dictionary
	total_stations = []
	for station in stations_query:
		station_dict = {}
		station_dict["Station"] = station.station
		station_dict["Station Name"] = station.name
		total_stations.append(station_dict)

	# Return a json list of stations from the dataset
	return jsonify(total_stations)

# Flask route for temperature observations analysis
@app.route("/api/v1.0/tobs")
def tobs():
	"""Returns a json list of tobs and which station it was observed by on which date"""
	# Find most recent date of records
	date_query = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
	date_query_results = list(np.ravel(date_query))
	date_split = date_query_results[0].split('-')
	current_year = dt.date(int(date_split[0]), int(date_split[1]), int(date_split[2]))

	# Design a query to retrieve the last 12 months of precipitation data.
	last_year = current_year - dt.timedelta(days=365)
	tobs_query = session.query(Measurement.station, Measurement.date, Measurement.tobs).\
							filter(Measurement.date > last_year).order_by(Measurement.date)
	
	# Convert query results to a Dictionary
	tobs_data = []
	for tobs in tobs_query:
		tobs_dict = {}
		tobs_dict["Station"] = tobs.station
		tobs_dict[tobs.date] = tobs.tobs
		tobs_data.append(tobs_dict)

	# Return a json list of Temperature Observations (tobs) for the previous year
	return jsonify(tobs_data)

# Flask route for daily normals with given start date
@app.route("/api/v1.0/<start>")
def daily_normals(start):
	"""Returns a json list of daily normals when given a start date"""
	# Convert search term into a datetime object
	start_date = dt.datetime.strptime(start, '%Y-%m-%d').date()

	# Calculate the daily normals. Normals are the averages for min, avg, and max temperatures.
	daily_calc = [func.min(Measurement.tobs),\
					func.avg(Measurement.tobs),\
					func.max(Measurement.tobs)]
	daily_query = session.query(Measurement.date,*daily_calc).\
				filter(func.strftime("%Y-%m-%d", Measurement.date) >= start_date).\
				group_by(Measurement.date)	

	# Convert query results into a dictionary
	daily_data = []
	for daily_normals in daily_query:
		(t_date, t_min, t_avg, t_max) = daily_normals
		norms_dict = {}
		norms_dict["Date"] = t_date
		norms_dict["Temp Min"] = t_min
		norms_dict["Temp Avg"] = t_avg
		norms_dict["Temp Max"] = t_max
		daily_data.append(norms_dict)

	# Return a json list of daily normals
	return jsonify(daily_data)			

@app.route("/api/v1.0/<start>/<end>")
def daily_normals2(start,end):
	"""Returns a json list of daily normals within a given range"""
	# Convert search terms into datetime objects
	start_date = dt.datetime.strptime(start, '%Y-%m-%d').date()
	end_date = dt.datetime.strptime(end, '%Y-%m-%d').date()

	# Calculate the daily normals. Normals are the averages for min, avg, and max temperatures
	daily_calc2 = [func.min(Measurement.tobs),\
					func.avg(Measurement.tobs),\
					func.max(Measurement.tobs)]
	daily_query2 = session.query(Measurement.date,*daily_calc2).\
				filter(func.strftime("%Y-%m-%d", Measurement.date) >= start_date).\
				filter(func.strftime("%Y-%m-%d", Measurement.date) <= end_date).\
				group_by(Measurement.date)

	# Convert query results into a json dictionary
	daily_data2 = []
	for daily_normals2 in daily_query2:
		(t_date2, t_min2, t_avg2, t_max2) = daily_normals2
		norms_dict2 = {}
		norms_dict2["Date"] = t_date2
		norms_dict2["Temp Min"] = t_min2
		norms_dict2["Temp Avg"] = t_avg2
		norms_dict2["Temp Max"] = t_max2
		daily_data2.append(norms_dict2)

	# Return a json list of dialy normals
	return jsonify(daily_data2)

# Define main behavior
if __name__ == ("__main__"):
	app.run(debug=True)
