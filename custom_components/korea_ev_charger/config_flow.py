"""Config flow for Korea EV Charger."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import (
    DOMAIN, 
    DEFAULT_RATES, 
    DEFAULT_CLIMATE_FEE, 
    DEFAULT_FUEL_FEE,
    DEFAULT_VAT_RATE,
    DEFAULT_FUND_RATE
)

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

        current_billing_date = opts.get("billing_date", self.config_entry.data.get("billing_date", 1))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                # 결제일
                vol.Required("billing_date", default=current_billing_date): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
                
                # 추가 요금 설정
                vol.Required("climate_fee", default=opts.get("climate_fee", DEFAULT_CLIMATE_FEE)): float,
                vol.Required("fuel_fee", default=opts.get("fuel_fee", DEFAULT_FUEL_FEE)): float,

                # 세금 및 기금 설정 (추가됨)
                vol.Required("vat_rate", default=opts.get("vat_rate", DEFAULT_VAT_RATE)): float,   # 부가세
                vol.Required("fund_rate", default=opts.get("fund_rate", DEFAULT_FUND_RATE)): float, # 전력기금

                # 계절별 단가
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