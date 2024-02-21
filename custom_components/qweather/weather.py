import logging
from datetime import timedelta
from .api import format_condition, FORECAST_DAILY_MAP_DAY, FORECAST_DAILY_MAP_NIGHT, FORECAST_HOURLY_MAP, FORECAST_NOW_MAP

from homeassistant.components.weather import Forecast, WeatherEntity, WeatherEntityFeature, ATTR_FORECAST_CONDITION, ATTR_FORECAST_IS_DAYTIME
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (ATTR_ATTRIBUTION, UnitOfPrecipitationDepth,
                                 UnitOfPressure, UnitOfSpeed,
                                 UnitOfTemperature)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN
from .hub import QWeatherHub

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub: QWeatherHub = hass.data[DOMAIN][config_entry.entry_id]

    await hub.async_update_weather_now()
    await hub.async_update_weather_hourly()
    await hub.async_update_weather_daily()

    async_track_time_interval(
        hass, hub.async_update_weather_now, timedelta(minutes=10))

    async_track_time_interval(
        hass, hub.async_update_weather_hourly, timedelta(minutes=15))

    async_track_time_interval(
        hass, hub.async_update_weather_daily, timedelta(hours=3))

    async_add_entities(
        [
            QWeather(hub),  # 每日天气预报
        ], True
    )


class QWeather(WeatherEntity):
    """和风天气实体定义"""

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS

    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_TWICE_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(
            self,
            hub: QWeatherHub
    ) -> None:
        self._hub: QWeatherHub = hub
        self._attr_unique_id = f"{self._hub.name}"
        self._attr_name = f"weather-{self._hub.name}"

    @property
    def attribution(self) -> str:
        return "来自和风天气的天气数据"

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def condition(self) -> str | None:
        return self._hub.weather.condition

    @property
    def native_temperature(self) -> float | None:
        return self._hub.weather.temperature

    @property
    def native_apparent_temperature(self) -> float | None:
        return self._hub.weather.apparent_temperature

    @property
    def native_dew_point(self) -> float | None:
        return self._hub.weather.dew_point

    @property
    def humidity(self) -> float | None:
        return float(self._hub.weather.humidity)

    @property
    def wind_bearing(self) -> float | None:
        return self._hub.weather.wind_bearing

    @property
    def native_wind_speed(self) -> float | None:
        return self._hub.weather.wind_speed

    @property
    def cloud_coverage(self) -> float | None:
        return self._hub.weather.cloud_coverage

    @property
    def native_visibility(self) -> float | None:
        return self._hub.weather.visibility

    @property
    def native_pressure(self) -> float | None:
        return self._hub.weather.pressure

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        if self.condition is not None:
            return {
                ATTR_ATTRIBUTION: self.attribution,
            }

    def __forecast_daily(self, item: dict, is_daytime: bool) -> dict[str] | None:
        ha_item_day = {
            k: item[v]
            for k, v in (FORECAST_DAILY_MAP_DAY if is_daytime else FORECAST_DAILY_MAP_NIGHT).items()
            if item.get(v) is not None
        }
        if ha_item_day.get(ATTR_FORECAST_CONDITION):
            ha_item_day[ATTR_FORECAST_CONDITION] = format_condition(
                ha_item_day[ATTR_FORECAST_CONDITION]
            )
        ha_item_day[ATTR_FORECAST_IS_DAYTIME] = is_daytime

        return ha_item_day

    async def async_forecast_twice_daily(self) -> list[Forecast] | None:
        forecast = self._hub.weather.daily_forecast

        ha_forecast: list[Forecast] = []
        for item in forecast:
            ha_forecast.append(self.__forecast_daily(item, True))
            ha_forecast.append(self.__forecast_daily(item, False))
        return ha_forecast

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        forecast = self._hub.weather.hourly_forecast

        ha_forecast: list[Forecast] = []
        for met_item in forecast:
            ha_item = {
                k: met_item[v]
                for k, v in FORECAST_HOURLY_MAP.items()
                if met_item.get(v) is not None
            }
            if ha_item.get(ATTR_FORECAST_CONDITION):
                ha_item[ATTR_FORECAST_CONDITION] = format_condition(
                    ha_item[ATTR_FORECAST_CONDITION]
                )
            ha_forecast.append(ha_item)
        return ha_forecast

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            name="天气预报",
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN,)},
            manufacturer="和风天气",
            model="Forecast",
            configuration_url="https://console.qweather.com/#/console",
        )
