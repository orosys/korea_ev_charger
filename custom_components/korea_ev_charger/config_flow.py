"""Config flow for Korea EV Charger."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import DOMAIN, DEFAULT_RATES

class KoreaEVChargerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="EV Charging Cost", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("source_sensor"): EntitySelector(
                    EntitySelectorConfig(domain="sensor", device_class="energy")
                ),
                vol.Required("voltage_type", default="low_voltage"): vol.In(
                    {"low_voltage": "저압 (Low Voltage)", "high_voltage": "고압 (High Voltage)"}
                ),
                vol.Required("billing_date", default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
                vol.Optional("holiday_sensor"): EntitySelector(
                    EntitySelectorConfig(domain="binary_sensor")
                ),
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler()

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for rate adjustments."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        voltage_type = self.config_entry.data.get("voltage_type", "low_voltage")
        defaults = DEFAULT_RATES[voltage_type]
        opts = self.config_entry.options

        # 현재 설정된 결제일 가져오기 (기본값 1일)
        # config_entry.data에 있을 수도 있고 options에 있을 수도 있음
        current_billing_date = opts.get("billing_date", self.config_entry.data.get("billing_date", 1))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                # 결제일 변경 옵션 추가
                vol.Required("billing_date", default=current_billing_date): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
                
                vol.Required("summer_max", default=opts.get("summer_max", defaults["summer"]["max"])): float,
                vol.Required("summer_mid", default=opts.get("summer_mid", defaults["summer"]["mid"])): float,
                vol.Required("summer_light", default=opts.get("summer_light", defaults["summer"]["light"])): float,
                
                vol.Required("sf_max", default=opts.get("sf_max", defaults["spring_fall"]["max"])): float,
                vol.Required("sf_mid", default=opts.get("sf_mid", defaults["spring_fall"]["mid"])): float,
                vol.Required("sf_light", default=opts.get("sf_light", defaults["spring_fall"]["light"])): float,
                
                vol.Required("winter_max", default=opts.get("winter_max", defaults["winter"]["max"])): float,
                vol.Required("winter_mid", default=opts.get("winter_mid", defaults["winter"]["mid"])): float,
                vol.Required("winter_light", default=opts.get("winter_light", defaults["winter"]["light"])): float,
            })
        )