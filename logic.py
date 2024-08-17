from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from gui import *
from api_location import *
from api_weatherdata import *
from datetime import datetime
import requests
import qtmodern.windows
import os


class Logic(QMainWindow, Ui_MainWindow):
    """
    Contains the logic that handles how the user interacts with the weather application.
    """
    # weather codes that have a corresponding icon
    VALID_CODES = ["0", "1", "2", "3", "45", "48", "51", "53", "55", "56", "57", "61", "63", "65", "66", "67",
                   "71", "73", "75", "77", "80", "81", "82", "85", "86", "95", "96", "99"]

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowType.Window |
                            Qt.WindowType.WindowMinimizeButtonHint |
                            Qt.WindowType.WindowCloseButtonHint)

        # empty dictionary to house various labels.
        # Easy solution since the gui file was largely generated via QT Designer
        self._labels = {'hourly': {
                            'time': [],
                            'img': [],
                            'temp': []
                            },
                        'daily': {
                            'day': [],
                            'precip': [],
                            'img': [],
                            'temps': []
                            }
                        }
        # create dictionary that links the APIs weather codes to their appropriate icons
        self._icons = {'0': "icons/clear_sky.png",
                       **{str(i): "icons/partly_cloudy.png" for i in [1, 2, 3]},
                       **{str(i): "icons/fog.png" for i in [45, 48]},
                       **{str(i): "icons/drizzle.png" for i in [51, 53, 55]},
                       **{str(i): "icons/freezing_rain.png" for i in [56, 57, 66, 67]},
                       **{str(i): "icons/rain.png" for i in [61, 63, 65]},
                       **{str(i): "icons/snow.png" for i in [71, 73, 75, 77, 85, 86]},
                       **{str(i): "icons/thunderstorm.png" for i in [80, 81, 82, 95, 96, 99]}
                       }
        # Validates the icon paths, setting the values to a generic blank image if the path does not exist.
        self._icons = {key: value if os.path.exists(value) else "<img>" for key, value in self._icons.items()}

        # add hourly labels to dictionary
        for i in range(12):
            self._labels['hourly']['time'].append(getattr(self, f'label_hourly_time_{i}'))
            self._labels['hourly']['img'].append(getattr(self, f'label_hourly_img_{i}'))
            self._labels['hourly']['temp'].append(getattr(self, f'label_hourly_temp_{i}'))

        # add daily labels to dictionary
        for i in range(7):
            self._labels['daily']['day'].append(getattr(self, f'label_daily_day_{i}'))
            self._labels['daily']['precip'].append(getattr(self, f'label_daily_precip_{i}'))
            self._labels['daily']['img'].append(getattr(self, f'label_daily_img_{i}'))
            self._labels['daily']['temps'].append(getattr(self, f'label_daily_temps_{i}'))

        self.pushButton_search.clicked.connect(self.search)
        self.coords, self.location, self.timezone = get_location()  # attempts to get a user's current location

        # if initial location not found (e.g. no internet connection), doesn't try to pull weather data
        if self.coords and self.location and self.timezone:
            self.display_weather_data()

    def validate_icon(self, label, weather_code) -> None:
        """
        Ensures all icons are pointed at valid paths. If not, sets the icon to a generic blank image.
        :param label: The name of the label
        :param weather_code: The weather code obtain from API
        """
        if weather_code in Logic.VALID_CODES:
            if self._icons[weather_code] != "<img>":
                label.setPixmap(QPixmap(
                    self._icons[weather_code]).scaled(label.width(), label.height()))
        else:
            label.setText("<img>")

    def search(self) -> None:
        """
        Takes the user-entered location and pulls location info from the open-meteo geocoding API.
        If applicable, sets the coords and timezone attributes to reflect the information obtained for that location.
        Note - only provides information for the most populous location for a given name (ex: users must enter a zip
        code to obtain weather location for a low population city that shares a name with a higher population city).
        If no location can be found, notifies the user accordingly with an error message.
        """
        location = self.lineEdit_city_Name.text()
        results = get_coordinates(location)

        if results:
            if 'country' in results[0]:
                if results[0]['country'] == 'United States':
                    self.location = f"{results[0]['name']}, {results[0]['admin1']}"
                else:
                    self.location = f"{results[0]['name']}"

            if 'latitude' in results[0] and 'longitude' in results[0]:
                self.coords = (results[0]['latitude'], results[0]['longitude'])
            if 'timezone' in results[0]:
                self.timezone = results[0]['timezone']

            if self.coords and self.location and self.timezone:
                self.display_weather_data()
        else:
            self.frame.setHidden(False)
            self.frame_weather_info.setHidden(True)
            self.label_location_error.setText("Could not find location.\nPlease try again.")

        self.lineEdit_city_Name.clear()

    def display_weather_data(self) -> None:
        """
        Uses the provided location and pulls the associated weather data from the API.
        Updates the labels to display the data accordingly.
        """
        current_weather, hourly_weather, daily_weather = (get_weather_data(
                                                            self.coords[0], self.coords[1], self.timezone))

        if current_weather is not None and hourly_weather is not None and daily_weather is not None:
            # set labels for current weather
            self.label_current_location.setText(self.location)
            self.label_today_temp.setText(f" {current_weather['temperature_2m']}°")
            self.label_today_feels_like.setText(f"Feels like {current_weather['apparent_temperature']}°")
            self.label_today_precip.setText(f"Precipitation:\n{current_weather['precipitation']} in")
            self.label_today_wind.setText(f"Wind Speed:\n{current_weather['wind_speed']} mph")
            self.label_today_humidity.setText(f"Humidity:\n{current_weather['humidity']}%")

            label = self.img_today_weather
            weather_code = f"{int(current_weather['weather_code'])}"

            # Assigns proper icons to corresponding labels
            self.validate_icon(label, weather_code)

            # set labels for hourly weather
            for i in range(12):
                self._labels['hourly']['time'][i].setText(f"{hourly_weather.iloc[i]['date']}")
                self._labels['hourly']['temp'][i].setText(f"{int(hourly_weather.iloc[i]['temperature_2m'])}°")

                label = self._labels['hourly']['img'][i]
                weather_code = f"{int(hourly_weather.iloc[i]['weather_code'])}"

                # Assigns proper icons to corresponding labels
                self.validate_icon(label, weather_code)

            # set labels for weekly forecast
            for i in range(7):
                if i == 0:  # sets the first label in the weekly forecast to "Today" if it corresponds to today
                    today = datetime.now().date().strftime("%Y-%m-%d")
                    self._labels['daily']['day'][i].setText("Today") if today == str(daily_weather.iloc[i]['date'])[:10] \
                        else f"{daily_weather.iloc[i]['date'].day_name()}"
                else:
                    self._labels['daily']['day'][i].setText(f"{daily_weather.iloc[i]['date'].day_name()}")
                self._labels['daily']['precip'][i].setText(f"{daily_weather.iloc[i]['precip_sum']:.2f} in")
                self._labels['daily']['temps'][i].setText(f"{int(daily_weather.iloc[i]['temp_max'])}°/"
                                                          f"{int(daily_weather.iloc[i]['temp_min'])}°")

                label = self._labels['daily']['img'][i]
                weather_code = f"{int(daily_weather.iloc[i]['weather_code'])}"

                # Assigns proper icons to corresponding labels
                self.validate_icon(label, weather_code)

            # hide the frame housing the location error message and shows the frame that displays the weather info
            self.frame.setHidden(True)
            self.frame_weather_info.setHidden(False)

        else:
            self.frame_weather_info.setHidden(True)
            self.label_location_error.setText("Could not retrieve weather data.\nPlease try again.")
            self.frame.setHidden(False)

    def keyPressEvent(self, event) -> None:
        """Overrides the existing method to simulate clicking the search button when a user hits Enter."""
        if event.key() == QtCore.Qt.Key.Key_Return or event.key() == QtCore.Qt.Key.Key_Enter:
            self.pushButton_search.click()
        else:
            super().keyPressEvent(event)  # for any other keys, ensures the event is handled normally

    def center(self) -> None:
        """
        Centers the gui on the screen, as qtmodern doesn't do so by default.
        """
        screen_geometry = self.screen().availableGeometry()
        window_geometry = self.frameGeometry()

        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())


class CustomModernWindow(qtmodern.windows.ModernWindow):
    """
    Customization changes for Modern Window Class
    """
    def setupUi(self) -> None:
        super().setupUi()  # Call the original setupUi method

        # Remove the maximize button from the title bar layout
        # qtmodern apparently shows this by default, and it maximizes the window even if the window size is fixed
        self.btnMaximize.hide()


def get_location() -> tuple[list[str] | None, str | None, str | None]:
    """
    Get the user's IP-based location.

    :returns:
        Tuple containing:
        - coords: Optional[List[str]]
            A list with latitude and longitude as strings, or None if there was an error.
        - location: Optional[str]
            A string with the city and region, or None if there was an error.
        - timezone: Optional[str]
            A string representing the timezone, or None if there was an error.
    """
    try:
        ip_info = requests.get('https://ipinfo.io').json()
        location = f"{ip_info['city']}, {ip_info['region']}"
        coords = ip_info['loc'].split(',')
        timezone = ip_info['timezone']
        return coords, location, timezone
    except Exception as e:
        print(f"Error fetching location: {e}")
        return None, None, None
