import logging
from datetime import timedelta
from collections.abc import Mapping
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_KEY, CONF_LOCATION, CONF_LOCATION_NAME
from .api import QWeatherClient, QWeatherData, QWeatherUpdateFeature

_LOGGER = logging.getLogger(__name__)


class QWeatherHub:
    """和风天气 Hub"""

    def __init__(self, hass: HomeAssistant, config: Mapping[str, Any]) -> None:
        self._hass_config: Mapping[str, Any] = config
        self._hass: HomeAssistant = hass

        key = config[CONF_KEY]
        location = config[CONF_LOCATION]
        self._name = config[CONF_LOCATION_NAME]

        if not key:
            _LOGGER.error("未设置 key")

        if not location:
            _LOGGER.error("未设置坐标")

        self._client: QWeatherClient = QWeatherClient(
            key, location)

    async def asnyc_setup(self) -> None:
        """初始化 hub"""
        try:
            await self.teardown()

        except Exception as exeption:
            msg = "Error during setup"
            _LOGGER.error(msg, exc_info=True)
            raise ConfigEntryNotReady(msg) from exeption

    async def teardown(self) -> None:
        """释放 hub 的占用的资源"""

    async def async_update_weather_now(self) -> None:
        await self._client.async_update_weather(QWeatherUpdateFeature.NOW)

    async def async_update_weather_hourly(self) -> None:
        await self._client.async_update_weather(QWeatherUpdateFeature.HOURLY)

    async def async_update_weather_daily(self) -> None:
        await self._client.async_update_weather(QWeatherUpdateFeature.DAILY)

    @property
    def name(self) -> str:
        return self._name

    @property
    def weather(self) -> QWeatherData:
        return self._client.weather
