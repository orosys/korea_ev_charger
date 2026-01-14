"""Config flow for Korea EV Charger."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .const import (
    DOMAIN, 
    DEFAULT_RATES, 
    DEFAULT_CLIMATE_FEE, 
    DEFAULT_FUEL_FEE,
    DEFAULT_VAT_RATE,
    DEFAULT_FUND_RATE,
    DEFAULT_CONTRACT_POWER,
    DEFAULT_SENSOR_NAME
)

class KoreaEVChargerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title=user_input.get("sensor_name", "EV Charging Cost"), data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("sensor_name", default=DEFAULT_SENSOR_NAME): TextSelector(),
                
                vol.Required("source_sensor"): EntitySelector(
                    EntitySelectorConfig(domain="sensor", device_class="energy")
                ),
                vol.Required("voltage_type", default="low_voltage"): vol.In(
                    {"low_voltage": "저압 (Low Voltage)", "high_voltage": "고압 (High Voltage)"}
                ),
                vol.Required("contract_power", default=DEFAULT_CONTRACT_POWER): NumberSelector(
                    NumberSelectorConfig(min=1, max=100, step=0.1, mode=NumberSelectorMode.BOX)
                ),
                vol.Required("billing_date", default=1): NumberSelector(
                    NumberSelectorConfig(min=1, max=31, step=1, mode=NumberSelectorMode.BOX)
                ),
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
        data = self.config_entry.data

        cur_bill_date = opts.get("billing_date", data.get("billing_date", 1))
        cur_contract = float(opts.get("contract_power", data.get("contract_power", DEFAULT_CONTRACT_POWER)))
        
        cur_clim = float(opts.get("climate_fee", DEFAULT_CLIMATE_FEE))
        cur_fuel = float(opts.get("fuel_fee", DEFAULT_FUEL_FEE))
        cur_vat = float(opts.get("vat_rate", DEFAULT_VAT_RATE))
        cur_fund = float(opts.get("fund_rate", DEFAULT_FUND_RATE))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("billing_date", default=cur_bill_date): NumberSelector(
                    NumberSelectorConfig(min=1, max=31, step=1, mode=NumberSelectorMode.BOX)
                ),
                vol.Required("contract_power", default=cur_contract): NumberSelector(
                    NumberSelectorConfig(min=1, max=100, step=0.1, mode=NumberSelectorMode.BOX)
                ),
                vol.Required("climate_fee", default=cur_clim): vol.Coerce(float),
                vol.Required("fuel_fee", default=cur_fuel): vol.Coerce(float),
                vol.Required("vat_rate", default=cur_vat): vol.Coerce(float),
                vol.Required("fund_rate", default=cur_fund): vol.Coerce(float),

                vol.Required("summer_max", default=float(opts.get("summer_max", defaults["summer"]["max"]))): vol.Coerce(float),
                vol.Required("summer_mid", default=float(opts.get("summer_mid", defaults["summer"]["mid"]))): vol.Coerce(float),
                vol.Required("summer_light", default=float(opts.get("summer_light", defaults["summer"]["light"]))): vol.Coerce(float),
                
                vol.Required("sf_max", default=float(opts.get("sf_max", defaults["spring_fall"]["max"]))): vol.Coerce(float),
                vol.Required("sf_mid", default=float(opts.get("sf_mid", defaults["spring_fall"]["mid"]))): vol.Coerce(float),
                vol.Required("sf_light", default=float(opts.get("sf_light", defaults["spring_fall"]["light"]))): vol.Coerce(float),
                
                vol.Required("winter_max", default=float(opts.get("winter_max", defaults["winter"]["max"]))): vol.Coerce(float),
                vol.Required("winter_mid", default=float(opts.get("winter_mid", defaults["winter"]["mid"]))): vol.Coerce(float),
                vol.Required("winter_light", default=float(opts.get("winter_light", defaults["winter"]["light"]))): vol.Coerce(float),
            })
        )