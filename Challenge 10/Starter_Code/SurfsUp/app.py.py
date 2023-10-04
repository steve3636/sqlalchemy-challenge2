from flask import Flask, jsonify
import datetime as dt
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

# Create an instance of Flask
app = Flask(__name__)

# Create engine to connect to the SQLite database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect the database into a new model
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to the Measurement and Station tables
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create a session (link) from Python to the DB
session = Session(engine)

# Define routes
@app.route("/")
def welcome():
    return (
        f"Welcome to the Climate App API!<br/><br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date (e.g., /api/v1.0/2017-01-01)<br/>"
        f"/api/v1.0/start_date/end_date (e.g., /api/v1.0/2017-01-01/2017-12-31)"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date one year from the last date in the data set
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_ago = most_recent_date - relativedelta(years=1)

    # Query precipitation data for the last year
    results = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= one_year_ago
    )

    # Convert the results to a dictionary
    precipitation_data = {date: prcp for date, prcp in results}

    return jsonify(precipitation_data)

@app.route("/api/v1.0/stations")
def stations():
    # Query stations
    results = session.query(Station.station).all()

    # Convert the results to a list of station names
    station_names = [station[0] for station in results]

    return jsonify(station_names)

@app.route("/api/v1.0/tobs")
def tobs():
    # Find the most active station
    most_active_station = (
        session.query(Measurement.station, func.count(Measurement.station))
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.station).desc())
        .first()
    )[0]

    # Calculate the date one year from the last date in the data set
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_ago = most_recent_date - relativedelta(years=1)

    # Query temperature observations for the most active station in the last year
    results = session.query(Measurement.date, Measurement.tobs).filter(
        Measurement.station == most_active_station,
        Measurement.date >= one_year_ago,
    )

    # Convert the results to a list of dictionaries
    temperature_data = [{"date": date, "temperature": tobs} for date, tobs in results]

    return jsonify(temperature_data)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start, end=None):
    try:
        # Convert start and end date strings to datetime objects
        start_date = dt.datetime.strptime(start, "%Y-%m-%d")
        end_date = (
            dt.datetime.strptime(end, "%Y-%m-%d") if end is not None else None
        )

        # Query to calculate temperature statistics based on start and end dates
        if end_date:
            results = (
                session.query(
                    func.min(Measurement.tobs),
                    func.avg(Measurement.tobs),
                    func.max(Measurement.tobs),
                )
                .filter(Measurement.date >= start_date, Measurement.date <= end_date)
                .all()
            )
        else:
            results = (
                session.query(
                    func.min(Measurement.tobs),
                    func.avg(Measurement.tobs),
                    func.max(Measurement.tobs),
                )
                .filter(Measurement.date >= start_date)
                .all()
            )

        # Extract the results
        tmin, tavg, tmax = results[0]

        # Create a dictionary with the temperature statistics
        temperature_stats = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d") if end_date else None,
            "tmin": tmin,
            "tavg": tavg,
            "tmax": tmax,
        }

        return jsonify(temperature_stats)

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
