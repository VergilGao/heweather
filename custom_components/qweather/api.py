import logging
import urllib.parse
from asyncio import TimeoutError as AsyncTimeoutError

from aiohttp import ClientError, ClientSession, ClientTimeout, TCPConnector

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY, ATTR_CONDITION_EXCEPTIONAL, ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL, ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY, ATTR_CONDITION_POURING, ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY, ATTR_CONDITION_SNOWY_RAINY, ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY, ATTR_CONDITION_WINDY_VARIANT,
    ATTR_FORECAST_CLOUD_COVERAGE, ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_DEW_POINT, ATTR_FORECAST_HUMIDITY,
    ATTR_FORECAST_NATIVE_PRECIPITATION, ATTR_FORECAST_NATIVE_PRESSURE,
    ATTR_FORECAST_NATIVE_TEMP, ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_SPEED, ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TIME, ATTR_FORECAST_UV_INDEX, ATTR_FORECAST_WIND_BEARING,
    ATTR_WEATHER_APPARENT_TEMPERATURE, ATTR_WEATHER_CLOUD_COVERAGE,
    ATTR_WEATHER_DEW_POINT, ATTR_WEATHER_HUMIDITY, ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE, ATTR_WEATHER_VISIBILITY,
    ATTR_WEATHER_WIND_BEARING, ATTR_WEATHER_WIND_SPEED)
from homeassistant.const import UnitOfTemperature

_LOGGER = logging.getLogger(__name__)

TEMP_CELSIUS: str = UnitOfTemperature.CELSIUS

API_URL: str = "https://devapi.qweather.com/v7/weather"

WEATHER_CONDITIONS_MAP = {
    ATTR_CONDITION_SUNNY: ["晴"],
    ATTR_CONDITION_CLOUDY: ["多云"],
    ATTR_CONDITION_PARTLYCLOUDY: ["少云", "晴间多云", "阴"],
    ATTR_CONDITION_WINDY: ["有风", "微风", "和风", "清风"],
    ATTR_CONDITION_WINDY_VARIANT: ["强风", "劲风", "疾风", "大风", "烈风", "飓风", "龙卷风", "热带风暴", "狂暴风", "风暴"],
    ATTR_CONDITION_RAINY: ["雨", "毛毛雨", "细雨", "小雨", "小到中雨", "中雨", "中到大雨", "大雨", "大到暴雨", "阵雨", "极端降雨", "冻雨"],
    ATTR_CONDITION_POURING: ["暴雨", "暴雨到大暴雨", "大暴雨", "大暴雨到特大暴雨", "特大暴雨", "强阵雨"],
    ATTR_CONDITION_LIGHTNING_RAINY: ["雷阵雨", "强雷阵雨"],
    ATTR_CONDITION_FOG: ["雾", "薄雾", "霾", "浓雾", "强浓雾", "中度霾", "重度霾", "严重霾", "大雾", "特强浓雾"],
    ATTR_CONDITION_HAIL: ["雷阵雨伴有冰雹"],
    ATTR_CONDITION_SNOWY: ["小雪", "小到中雪", "中雪", "中到大雪", "大雪", "大到暴雪", "暴雪", "阵雪"],
    ATTR_CONDITION_SNOWY_RAINY: ["雨夹雪", "雨雪天气", "阵雨夹雪"],
    ATTR_CONDITION_EXCEPTIONAL: ["扬沙", "浮尘", "沙尘暴", "强沙尘暴", "未知"],
}

FORECAST_NOW_MAP = {
    ATTR_FORECAST_CONDITION: "text",  # 天气
    ATTR_WEATHER_TEMPERATURE: "temp",  # 温度
    ATTR_WEATHER_APPARENT_TEMPERATURE: "feelsLike",  # 体感温度
    ATTR_WEATHER_DEW_POINT: "dew",  # 露点温度
    ATTR_WEATHER_WIND_BEARING: "wind360",  # 风向
    ATTR_WEATHER_WIND_SPEED: "windSpeed",  # 风力
    ATTR_WEATHER_CLOUD_COVERAGE: "cloud",  # 云量
    ATTR_WEATHER_HUMIDITY: "humidity",  # 湿度
    ATTR_WEATHER_VISIBILITY: "vis",  # 能见度
    ATTR_WEATHER_PRESSURE: "pressure",  # 大气压强
}

FORECAST_HOURLY_MAP = {
    ATTR_FORECAST_CONDITION: "text",  # 天气
    ATTR_FORECAST_NATIVE_PRECIPITATION: "precip",  # 降雨量
    ATTR_FORECAST_PRECIPITATION_PROBABILITY: "pop",  # 降雨概率
    ATTR_FORECAST_NATIVE_TEMP: "temp",  # 温度
    ATTR_FORECAST_DEW_POINT: "dew",  # 露点温度
    ATTR_FORECAST_TIME: "fxTime",  # 预报时间
    ATTR_FORECAST_WIND_BEARING: "wind360",  # 风向
    ATTR_FORECAST_NATIVE_WIND_SPEED: "windSpeed",  # 风力
    ATTR_FORECAST_CLOUD_COVERAGE: "cloud",  # 云量
    ATTR_FORECAST_HUMIDITY: "humidity",  # 湿度
    ATTR_FORECAST_NATIVE_PRESSURE: "pressure",  # 大气压强
}

FORECAST_DAILY_MAP_DAY = {
    ATTR_FORECAST_CONDITION: "textDay",  # 白天的天气
    ATTR_FORECAST_NATIVE_PRECIPITATION: "precip",  # 总降雨量
    ATTR_FORECAST_NATIVE_TEMP: "tempMax",  # 最高温度
    ATTR_FORECAST_NATIVE_TEMP_LOW: "tempMin",  # 最低温度
    ATTR_FORECAST_TIME: "fxDate",  # 预报日期
    ATTR_FORECAST_WIND_BEARING: "wind360Day",  # 风向
    ATTR_FORECAST_NATIVE_WIND_SPEED: "windSpeedDay",  # 风速
    ATTR_FORECAST_CLOUD_COVERAGE: "cloud",  # 云量
    ATTR_FORECAST_HUMIDITY: "humidity",  # 湿度
    ATTR_FORECAST_NATIVE_PRESSURE: "pressure",  # 大气压强
    ATTR_FORECAST_UV_INDEX: "uvIndex",  # 紫外线强度指数
}

FORECAST_DAILY_MAP_NIGHT = {
    ATTR_FORECAST_CONDITION: "textNight",  # 夜间的天气
    ATTR_FORECAST_NATIVE_PRECIPITATION: "precip",  # 总降雨量
    ATTR_FORECAST_NATIVE_TEMP: "tempMax",  # 最高温度
    ATTR_FORECAST_NATIVE_TEMP_LOW: "tempMin",  # 最低温度
    ATTR_FORECAST_TIME: "fxDate",  # 预报日期
    ATTR_FORECAST_WIND_BEARING: "wind360Night",  # 风向
    ATTR_FORECAST_NATIVE_WIND_SPEED: "windSpeedNight",  # 风速
    ATTR_FORECAST_CLOUD_COVERAGE: "cloud",  # 云量
    ATTR_FORECAST_HUMIDITY: "humidity",  # 湿度
    ATTR_FORECAST_NATIVE_PRESSURE: "pressure",  # 大气压强
    ATTR_FORECAST_UV_INDEX: "uvIndex",  # 紫外线强度指数
}

CONDITION_CLASSES = {
    'sunny': ["晴"],
    'cloudy': ["多云"],
    'partlycloudy': ["少云", "晴间多云", "阴"],
    'windy': ["有风", "微风", "和风", "清风"],
    'windy-variant': ["强风", "劲风", "疾风", "大风", "烈风"],
    'hurricane': ["飓风", "龙卷风", "热带风暴", "狂暴风", "风暴"],
    'rainy': ["雨", "毛毛雨", "细雨", "小雨", "小到中雨", "中雨", "中到大雨", "大雨", "大到暴雨", "阵雨", "极端降雨", "冻雨"],
    'pouring': ["暴雨", "暴雨到大暴雨", "大暴雨", "大暴雨到特大暴雨", "特大暴雨", "强阵雨"],
    'lightning-rainy': ["雷阵雨", "强雷阵雨"],
    'fog': ["雾", "薄雾", "霾", "浓雾", "强浓雾", "中度霾", "重度霾", "严重霾", "大雾", "特强浓雾"],
    'hail': ["雷阵雨伴有冰雹"],
    'snowy': ["小雪", "小到中雪", "中雪", "中到大雪", "大雪", "大到暴雪", "暴雪", "阵雪"],
    'snowy-rainy': ["雨夹雪", "雨雪天气", "阵雨夹雪"],
    'exceptional': ["扬沙", "浮尘", "沙尘暴", "强沙尘暴", "未知"],
}


def format_condition(condition: str) -> str:
    for key, value in WEATHER_CONDITIONS_MAP.items():
        if condition in value:
            return key
    return condition


class QWeatherData:
    """存储从和风天气API查询到的天气数据"""

    def __init__(self) -> None:
        self.__current_weather_data: dict = {}
        self.daily_forecast: list[dict] = []
        self.hourly_forecast: list[dict] = []

    def update_weather_now(self, data: dict) -> None:
        weather_data = {}
        weather_data[ATTR_FORECAST_CONDITION] = data.get(
            FORECAST_NOW_MAP[ATTR_FORECAST_CONDITION])
        weather_data[ATTR_WEATHER_TEMPERATURE] = (
            FORECAST_NOW_MAP[ATTR_FORECAST_CONDITION])

        self.__current_weather_data = data

    def update_weather_hourly(self, data: list[dict]) -> None:
        self.hourly_forecast = data

    def update_weather_daily(self, data: list[dict]) -> None:
        self.daily_forecast = data

    @property
    def condition(self) -> str | None:
        return self.__current_weather_data.get(FORECAST_NOW_MAP[ATTR_FORECAST_CONDITION])

    @property
    def temperature(self) -> float | None:
        return self.__current_weather_data.get(FORECAST_NOW_MAP[ATTR_WEATHER_TEMPERATURE])

    @property
    def apparent_temperature(self) -> float | None:
        return self.__current_weather_data.get(FORECAST_NOW_MAP[ATTR_WEATHER_APPARENT_TEMPERATURE])

    @property
    def dew_point(self) -> float | None:
        return self.__current_weather_data.get(FORECAST_NOW_MAP[ATTR_WEATHER_DEW_POINT])

    @property
    def wind_bearing(self) -> int | None:
        return self.__current_weather_data.get(FORECAST_NOW_MAP[ATTR_WEATHER_WIND_BEARING])

    @property
    def wind_speed(self) -> int | None:
        return self.__current_weather_data.get(FORECAST_NOW_MAP[ATTR_WEATHER_WIND_SPEED])

    @property
    def cloud_coverage(self) -> float | None:
        return self.__current_weather_data.get(FORECAST_NOW_MAP[ATTR_WEATHER_CLOUD_COVERAGE])

    @property
    def humidity(self) -> float | None:
        return self.__current_weather_data.get(FORECAST_NOW_MAP[ATTR_WEATHER_HUMIDITY])

    @property
    def visibility(self) -> float | None:
        return self.__current_weather_data.get(FORECAST_NOW_MAP[ATTR_WEATHER_VISIBILITY])

    @property
    def pressure(self) -> float | None:
        return self.__current_weather_data.get(FORECAST_NOW_MAP[ATTR_WEATHER_PRESSURE])


class QWeatherUpdateFeature:
    NOW = 1
    HOURLY = 2
    DAILY = 3


def __nameof_feature(feature: QWeatherUpdateFeature) -> str:
    match feature:
        case QWeatherUpdateFeature.NOW:
            return "now"
        case QWeatherUpdateFeature.HOURLY:
            return "hourly"
        case QWeatherUpdateFeature.DAILY:
            return "daily"
        case _:
            return ""


class QWeatherClient:
    """和风天气客户端"""

    def __init__(self, key: str, location: str) -> None:
        data = {
            "location": location,
            "key": key
        }

        query_string = urllib.parse.urlencode(data)
        self._weather_days = f"{API_URL}/7d?{query_string}"
        self._weather_hourly = f"{API_URL}/24h?{query_string}"
        self._weather_now_url = f"{API_URL}/now?{query_string}"
        self._weather = QWeatherData()

    async def async_update_weather(self, feature: QWeatherUpdateFeature) -> None:
        """更新天气数据"""

        _LOGGER.info("Update weather data from qweather")

        try:
            async with ClientSession(connector=TCPConnector(limit=10), timeout=ClientTimeout(total=20)) as session:
                match feature:
                    case QWeatherUpdateFeature.NOW:
                        async with session.get(self._weather_now_url) as response:
                            data = await response.json()
                            weather: dict = data["now"]
                            self._weather.update_weather_now(weather)
                    case QWeatherUpdateFeature.HOURLY:
                        async with session.get(self._weather_hourly) as response:
                            data = await response.json()
                            forecast: list[dict] = data["hourly"]
                            self._weather.update_weather_hourly(forecast)
                    case QWeatherUpdateFeature.DAILY:
                        async with session.get(self._weather_days) as response:
                            data = await response.json()
                            forecast: list[dict] = data["daily"]
                            self._weather.update_weather_daily(forecast)
        except (ClientError, AsyncTimeoutError):
            _LOGGER.error(
                f"Error while update weather in {__nameof_feature(feature)}")
            return

    @property
    def weather(self) -> QWeatherData:
        return self._weather
