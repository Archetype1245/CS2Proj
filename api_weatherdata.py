import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def get_weather_data(lat, long, timezone):
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": long,
        "current": ["temperature_2m", "apparent_temperature", "precipitation", "weather_code", "relative_humidity_2m",
                    "wind_speed_10m"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "apparent_temperature", "precipitation", "weather_code",
                   "wind_speed_10m"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max",
                  "apparent_temperature_min", "precipitation_sum"],
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timeformat": "unixtime",
        "timezone": timezone
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Current values. The order of variables needs to be the same as requested.
    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_apparent_temperature = current.Variables(1).Value()
    current_precipitation = current.Variables(2).Value()
    current_weather_code = current.Variables(3).Value()
    current_humidity = current.Variables(4).Value()
    current_wind_speed = current.Variables(5).Value()

    current_data = {"temperature_2m": str(int(current_temperature_2m)),
                    "apparent_temperature": str(int(current_apparent_temperature)),
                    "precipitation": f"{current_precipitation:.2f}",
                    "weather_code": current_weather_code,
                    "humidity": str(int(current_humidity)),
                    "wind_speed": str(int(current_wind_speed))}

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_apparent_temperature = hourly.Variables(2).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(3).ValuesAsNumpy()
    hourly_weather_code = hourly.Variables(4).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(5).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                                         end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                                         freq=pd.Timedelta(seconds=hourly.Interval()),
                                         inclusive="left"
                                         ),
                   "temperature_2m": hourly_temperature_2m,
                   "relative_humidity_2m": hourly_relative_humidity_2m,
                   "apparent_temperature": hourly_apparent_temperature,
                   "precipitation": hourly_precipitation,
                   "weather_code": hourly_weather_code,
                   "wind_speed_10m": hourly_wind_speed_10m}

    hourly_dataframe = pd.DataFrame(data=hourly_data)

    local_tz = ZoneInfo(timezone)
    hourly_dataframe['date'] = pd.to_datetime(hourly_dataframe['date'], utc=True).dt.tz_convert(local_tz)

    current_time = datetime.now(local_tz).replace(minute=0, second=0, microsecond=0)
    end_time = current_time + timedelta(hours=12)

    hourly_dataframe = hourly_dataframe[
        (hourly_dataframe['date'] >= current_time) & (hourly_dataframe['date'] < end_time)]

    hourly_dataframe['date'] = hourly_dataframe['date'].dt.strftime('%I:%M %p').str.lstrip('0')

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()
    daily_apparent_temperature_max = daily.Variables(3).ValuesAsNumpy()
    daily_apparent_temperature_min = daily.Variables(4).ValuesAsNumpy()
    daily_precip = daily.Variables(5).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"),
        "weather_code": daily_weather_code,
        "temp_max": daily_temperature_2m_max,
        "temp_min": daily_temperature_2m_min,
        "apparent_temperature_max": daily_apparent_temperature_max,
        "apparent_temperature_min": daily_apparent_temperature_min,
        "precip_sum": daily_precip}

    daily_dataframe = pd.DataFrame(data=daily_data)
    daily_dataframe['date'] = pd.to_datetime(daily_dataframe['date'], utc=True).dt.tz_convert(local_tz)
    # print(daily_dataframe)

    return current_data, hourly_dataframe, daily_dataframe


if __name__ == "__main__":
    lat, long, timezone = 41.25626, -95.94043, 'America/Chicago'
    get_weather_data(lat,long, timezone)