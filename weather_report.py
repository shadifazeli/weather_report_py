# 날씨 예보 프로그램 (Open-Meteo API)
# GitHub Repository:
# https://github.com/shadifazeli/weather_report_py.git
#
# 기능
# - 한국어 / 영어 출력 선택
# - 사용자가 지역을 입력하면 해당 지역의 위도/경도를 검색
# - 오늘부터 3일 동안 오전 6시 / 오후 3시 날씨 표시
# - 일일 최저 / 최고 기온 표시
# - 원하면 받아온 날씨 정보를 JSON 파일로 저장

import json
from datetime import datetime
from pathlib import Path

import requests


DEFAULT_CITY = "Cheonan"
FORECAST_DAYS = 3
TARGET_HOURS = (6, 15)


WEATHER_CODES = {
    0: {"ko": "맑음", "en": "Clear"},
    1: {"ko": "대체로 맑음", "en": "Mostly clear"},
    2: {"ko": "부분적으로 흐림", "en": "Partly cloudy"},
    3: {"ko": "흐림", "en": "Overcast"},
    45: {"ko": "안개", "en": "Fog"},
    48: {"ko": "서리 안개", "en": "Rime fog"},
    51: {"ko": "약한 이슬비", "en": "Light drizzle"},
    53: {"ko": "이슬비", "en": "Drizzle"},
    55: {"ko": "강한 이슬비", "en": "Heavy drizzle"},
    56: {"ko": "약한 어는 이슬비", "en": "Light freezing drizzle"},
    57: {"ko": "강한 어는 이슬비", "en": "Heavy freezing drizzle"},
    61: {"ko": "약한 비", "en": "Light rain"},
    63: {"ko": "비", "en": "Rain"},
    65: {"ko": "강한 비", "en": "Heavy rain"},
    66: {"ko": "약한 어는 비", "en": "Light freezing rain"},
    67: {"ko": "강한 어는 비", "en": "Heavy freezing rain"},
    71: {"ko": "약한 눈", "en": "Light snow"},
    73: {"ko": "눈", "en": "Snow"},
    75: {"ko": "강한 눈", "en": "Heavy snow"},
    77: {"ko": "싸락눈", "en": "Snow grains"},
    80: {"ko": "약한 소나기", "en": "Light rain showers"},
    81: {"ko": "소나기", "en": "Rain showers"},
    82: {"ko": "강한 소나기", "en": "Heavy rain showers"},
    85: {"ko": "약한 눈 소나기", "en": "Light snow showers"},
    86: {"ko": "강한 눈 소나기", "en": "Heavy snow showers"},
    95: {"ko": "뇌우", "en": "Thunderstorm"},
    96: {"ko": "우박을 동반한 뇌우", "en": "Thunderstorm with hail"},
    99: {"ko": "강한 우박을 동반한 뇌우", "en": "Thunderstorm with heavy hail"},
}


TEXT = {
    "ko": {
        "program_title": "🌤️ 날씨 예보 프로그램 (Open-Meteo API)",
        "program_info": "오전 6시, 오후 3시 기준으로 3일간 날씨를 제공합니다.",
        "city_prompt": f"날씨를 확인할 지역을 입력하세요 (기본값: {DEFAULT_CITY}): ",
        "location_not_found": "❌ 해당 지역을 찾을 수 없습니다.",
        "fetching": "📍 {name} (위도: {lat}, 경도: {lon})의 날씨 정보를 가져옵니다...",
        "forecast_title": "🌤️  {name} 날씨 예보 (오전 6시 / 오후 3시 기준)",
        "today": "오늘",
        "tomorrow": "내일",
        "day_after": "모레",
        "missing": "{hour:02d}:00 정보를 찾을 수 없습니다.",
        "am": "오전",
        "pm": "오후",
        "weather": "날씨",
        "temperature": "기온",
        "precipitation": "강수확률",
        "humidity": "습도",
        "wind": "풍속",
        "daily_temp": "🌡️ 일일 기온: 최저 {min_temp:.0f} °C / 최고 {max_temp:.0f} °C",
        "save_prompt": "\n날씨 정보를 JSON 파일로 저장하시겠습니까? (y/n): ",
        "saved": "✅ 저장 완료: {filename}",
        "not_saved": "저장하지 않고 프로그램을 종료합니다.",
        "request_error": "❌ 인터넷 또는 API 연결 오류가 발생했습니다: {error}",
        "data_error": "❌ 날씨 데이터를 처리하는 중 오류가 발생했습니다: {error}",
    },
    "en": {
        "program_title": "🌤️ Weather Forecast Program (Open-Meteo API)",
        "program_info": "Shows a 3-day forecast for 06:00 and 15:00.",
        "city_prompt": f"Enter a city (default: {DEFAULT_CITY}): ",
        "location_not_found": "❌ Location not found.",
        "fetching": "📍 Fetching weather for {name} (lat: {lat}, lon: {lon})...",
        "forecast_title": "🌤️  {name} Weather Forecast (06:00 / 15:00)",
        "today": "Today",
        "tomorrow": "Tomorrow",
        "day_after": "Day after tomorrow",
        "missing": "Could not find data for {hour:02d}:00.",
        "am": "AM",
        "pm": "PM",
        "weather": "Weather",
        "temperature": "Temperature",
        "precipitation": "Precipitation",
        "humidity": "Humidity",
        "wind": "Wind speed",
        "daily_temp": "🌡️ Daily temperature: min {min_temp:.0f} °C / max {max_temp:.0f} °C",
        "save_prompt": "\nSave the weather data as a JSON file? (y/n): ",
        "saved": "✅ Saved: {filename}",
        "not_saved": "Exiting without saving.",
        "request_error": "❌ Internet or API connection error: {error}",
        "data_error": "❌ Error while processing weather data: {error}",
    },
}


def choose_language():
    print("출력 언어를 선택하세요. / Select output language.")
    print("1. 한국어")
    print("2. English")
    choice = input("선택 / Choice (기본값 / default: 1): ").strip()
    return "en" if choice == "2" else "ko"


def get_location(city, lang):
    """Open-Meteo Geocoding API로 지역의 위도/경도를 찾는다."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city,
        "count": 1,
        "language": lang,
        "format": "json",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    results = data.get("results", [])
    if not results:
        return None

    result = results[0]
    return {
        "name": result.get("name", city),
        "country": result.get("country", ""),
        "admin1": result.get("admin1", ""),
        "latitude": result["latitude"],
        "longitude": result["longitude"],
    }


def get_weather(latitude, longitude):
    """Open-Meteo Forecast API에서 3일간 날씨 정보를 가져온다."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation_probability",
                "weather_code",
                "wind_speed_10m",
            ]
        ),
        "daily": "temperature_2m_max,temperature_2m_min",
        "forecast_days": FORECAST_DAYS,
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def day_label(index, lang):
    if index == 0:
        return TEXT[lang]["today"]
    if index == 1:
        return TEXT[lang]["tomorrow"]
    return TEXT[lang]["day_after"]


def weather_text(code, lang):
    descriptions = WEATHER_CODES.get(code)
    if descriptions:
        return descriptions[lang]
    return f"날씨 코드 {code}" if lang == "ko" else f"Weather code {code}"


def find_hourly_index(hourly_times, date_string, hour):
    target = f"{date_string}T{hour:02d}:00"
    try:
        return hourly_times.index(target)
    except ValueError:
        return None


def print_forecast(location, weather, lang):
    t = TEXT[lang]
    hourly = weather["hourly"]
    daily = weather["daily"]

    print()
    print("=" * 58)
    print(t["forecast_title"].format(name=location["name"]))
    print("=" * 58)

    for day_index, date_string in enumerate(daily["time"]):
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        short_date = date_obj.strftime("%m.%d.")

        print()
        print(f"🗓️ {day_label(day_index, lang)} ({short_date})")
        print("-" * 50)

        for hour in TARGET_HOURS:
            idx = find_hourly_index(hourly["time"], date_string, hour)

            if idx is None:
                print(t["missing"].format(hour=hour))
                continue

            period = t["am"] if hour < 12 else t["pm"]
            temperature = hourly["temperature_2m"][idx]
            humidity = hourly["relative_humidity_2m"][idx]
            rain_probability = hourly["precipitation_probability"][idx]
            weather_code = hourly["weather_code"][idx]
            wind_speed = hourly["wind_speed_10m"][idx]

            print(f"🌅 {period} {hour:02d}:00")
            print(f"   {t['weather']}: {weather_text(weather_code, lang)}")
            print(f"   {t['temperature']}: {temperature:.0f} °C")
            print(f"   {t['precipitation']}: {rain_probability:.0f}%")
            print(f"   {t['humidity']}: {humidity:.0f}%")
            print(f"   {t['wind']}: {wind_speed:.0f} km/h")
            print()

        min_temp = daily["temperature_2m_min"][day_index]
        max_temp = daily["temperature_2m_max"][day_index]
        print(t["daily_temp"].format(min_temp=min_temp, max_temp=max_temp))
        print()
        print("=" * 58)


def save_json(location, weather, lang):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_city = location["name"].replace(" ", "_")
    filename = Path(f"weather_{safe_city}_{now}.json")

    output = {
        "location": location,
        "weather": weather,
    }

    with filename.open("w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=4)

    print(TEXT[lang]["saved"].format(filename=filename))


def main():
    lang = choose_language()
    t = TEXT[lang]

    print()
    print(t["program_title"])
    print(t["program_info"])
    print("-" * 58)

    city = input(t["city_prompt"]).strip()
    if not city:
        city = DEFAULT_CITY

    try:
        location = get_location(city, lang)

        if location is None:
            print(t["location_not_found"])
            return

        print(
            "\n"
            + t["fetching"].format(
                name=location["name"],
                lat=location["latitude"],
                lon=location["longitude"],
            )
        )

        weather = get_weather(location["latitude"], location["longitude"])
        print_forecast(location, weather, lang)

        answer = input(t["save_prompt"]).strip().lower()
        if answer == "y":
            save_json(location, weather, lang)
        else:
            print(t["not_saved"])

    except requests.RequestException as error:
        print(t["request_error"].format(error=error))
    except (KeyError, IndexError, TypeError, ValueError) as error:
        print(t["data_error"].format(error=error))


if __name__ == "__main__":
    main()
