import requests


def get_coordinates(location):
    # Base URL for Open-Meteo's Geocoding API
    base_url = "https://geocoding-api.open-meteo.com/v1/search"

    # Construct the complete URL with query parameters
    params = {
        'name': location,
        'count': 1,  # Limit the results to the top result only
        'language': 'en',
        'format': 'json'
    }

    # Make the request
    try:
        response = requests.get(base_url, params=params)
    except Exception as e:
        print(f"Error fetching location: {e}")
        return None

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

        if 'results' in data and len(data['results']) > 0:
            # Extract the first result's coordinates
            results = data['results']
            return results
        else:
            return None
    else:
        return None


if __name__ == "__main__":
    location = input("Enter city name or ZIP code: ")
    results = get_coordinates(location)

    if results is not None:
        print(results)

        for result in results:
            name = result.get('name')
            country = result.get('country')
            latitude = result.get('latitude')
            longitude = result.get('longitude')
            timezone = result.get('timezone')
            population = result.get('population')
            state = result.get('admin1') if country == "United States" else None

            print(f"{name}, {state + ', ' if state else ''}{country}, {latitude}, {longitude}, {timezone}")

    else:
        print("Location not found, please check the name or ZIP code and try again.")