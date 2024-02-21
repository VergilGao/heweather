import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.helpers import selector

from .const import (
    CONF_KEY,
    CONF_LOCATION,
    CONF_LOCATION_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class QWeatherConfigFlow(ConfigFlow, domain=DOMAIN):
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._entry: ConfigEntry | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "QWeatherOptionFlowHander":
        return QWeatherOptionFlowHander(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}
        data = {}

        if user_input is not None:
            data.update(user_input)
            if len(data[CONF_LOCATION_NAME]) < 1:
                errors[CONF_LOCATION_NAME] = "invalid_name"
            if len(data[CONF_KEY]) != 32:
                errors[CONF_KEY] = "invalid_key"
            if not str(data[CONF_LOCATION]).isdigit():
                errors[CONF_LOCATION] = "invalid_location"

            if not errors:
                if self._entry:
                    self.hass.config_entries.async_update_entry(
                        self._entry, data=data)
                    self.hass.async_create_task(
                        self.hass.config_entries.async_reload(
                            self._entry.entry_id)
                    )
                    return self.async_abort(reason="reauth_successful")

                self._async_abort_entries_match(
                    {CONF_LOCATION_NAME: user_input[CONF_LOCATION_NAME]}
                )

                self._data.update(data)
                return self.async_create_entry(
                    title=self._data[CONF_LOCATION_NAME],
                    data=self._data,
                    options=user_input,
                )

        if self._entry:
            data.update(self._entry.data)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOCATION_NAME): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(CONF_LOCATION): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(CONF_KEY): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD
                        )
                    ),
                }
            ),
            errors=errors,
        )


class QWeatherOptionFlowHander(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}

        if user_input is not None:
            try:
                if len(user_input[CONF_KEY]) < 1:
                    errors[CONF_KEY] = "setup_key"
                else:
                    return self.async_create_entry(
                        title=self._config_entry.title,
                        data=user_input,
                    )
            except Exception:  # pylint: disable=broad-except
                _LOGGER.error("Unexpected exception", exc_info=True)
                errors["base"] = "unknown"
