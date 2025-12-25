"""Sensor platform for Korea EV Charger with taxes and extra fees."""
from datetime import datetime
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
import homeassistant.util.dt as dt_util
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    DOMAIN, 
    SEASONS, 
    TIME_ZONES, 
    DEFAULT_RATES, 
    DEFAULT_CLIMATE_FEE, 
    DEFAULT_FUEL_FEE,
    DEFAULT_VAT_RATE,
    DEFAULT_FUND_RATE
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor."""
    source_sensor = config_entry.data["source_sensor"]
    voltage_type = config_entry.data.get("voltage_type", "low_voltage")
    holiday_sensor = config_entry.data.get("holiday_sensor")
    
    billing_date = config_entry.options.get("billing_date", config_entry.data.get("billing_date", 1))
    
    sensor = KoreaEVCostSensor(hass, source_sensor, voltage_type, holiday_sensor, billing_date, config_entry)
    async_add_entities([sensor])

class KoreaEVCostSensor(RestoreEntity, SensorEntity):
    """Calculates cost based on TOU rates including taxes."""

    _attr_has_entity_name = True
    _attr_name = "EV Charging Cost"
    _attr_native_unit_of_measurement = "KRW"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, hass, source_entity, voltage_type, holiday_sensor, billing_date, config_entry):
        """Initialize the sensor."""
        self.hass = hass
        self._source_entity = source_entity
        self._voltage_type = voltage_type
        self._holiday_sensor = holiday_sensor
        self._billing_date = billing_date
        self._config_entry = config_entry
        self._state = 0.0
        self._last_energy = None
        
        self._current_price = 0
        self._current_load_level = "Unknown"
        self._current_season = "Unknown"

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            try:
                self._state = float(last_state.state)
            except ValueError:
                self._state = 0.0

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._source_entity], self._handle_energy_change
            )
        )

        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_monthly_base_rate_update, hour=0, minute=0, second=1
            )
        )

    def _get_tax_multiplier(self):
        """Calculate total tax multiplier from options."""
        opts = self._config_entry.options
        vat_rate = opts.get("vat_rate", DEFAULT_VAT_RATE)
        fund_rate = opts.get("fund_rate", DEFAULT_FUND_RATE)
        
        # 합계 승수 = 1 + (부가세율/100) + (기금율/100)
        # 예: 1 + 0.1 + 0.037 = 1.137
        return 1 + (vat_rate / 100.0) + (fund_rate / 100.0)

    async def _async_monthly_base_rate_update(self, now):
        """Add full monthly base rate with tax."""
        if now.day != self._billing_date:
            return

        base_rate = DEFAULT_RATES[self._voltage_type]["base"]
        
        # 세금 승수 가져오기
        tax_multiplier = self._get_tax_multiplier()
        
        # 기본요금에도 세금 적용
        final_base_rate = base_rate * tax_multiplier
        
        self._state += final_base_rate
        _LOGGER.debug("Monthly base rate added: %f KRW (Multiplier: %f)", final_base_rate, tax_multiplier)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {
            "current_price_per_kwh": self._current_price,
            "load_level": self._current_load_level,
            "season": self._current_season,
            "source_sensor": self._source_entity,
            "base_rate_type": self._voltage_type,
            "billing_date": self._billing_date
        }

    @property
    def native_value(self):
        return round(self._state, 2)

    def _get_current_rates(self):
        defaults = DEFAULT_RATES[self._voltage_type]
        opts = self._config_entry.options
        
        self._billing_date = opts.get("billing_date", self._billing_date)
        
        climate_fee = opts.get("climate_fee", DEFAULT_CLIMATE_FEE)
        fuel_fee = opts.get("fuel_fee", DEFAULT_FUEL_FEE)

        rates = {
            "summer": {
                "max": opts.get("summer_max", defaults["summer"]["max"]),
                "mid": opts.get("summer_mid", defaults["summer"]["mid"]),
                "light": opts.get("summer_light", defaults["summer"]["light"]),
            },
            "spring_fall": {
                "max": opts.get("sf_max", defaults["spring_fall"]["max"]),
                "mid": opts.get("sf_mid", defaults["spring_fall"]["mid"]),
                "light": opts.get("sf_light", defaults["spring_fall"]["light"]),
            },
            "winter": {
                "max": opts.get("winter_max", defaults["winter"]["max"]),
                "mid": opts.get("winter_mid", defaults["winter"]["mid"]),
                "light": opts.get("winter_light", defaults["winter"]["light"]),
            }
        }
        return rates, climate_fee, fuel_fee

    def _determine_season_and_load(self, now):
        month = now.month
        hour = now.hour
        weekday = now.weekday()
        
        if month in SEASONS["summer"]:
            season_key = "summer"
            time_key = "summer_spring_fall"
        elif month in SEASONS["winter"]:
            season_key = "winter"
            time_key = "winter"
        else:
            season_key = "spring_fall"
            time_key = "summer_spring_fall"
            
        self._current_season = season_key

        is_holiday = False
        if weekday == 6:
            is_holiday = True
        elif self._holiday_sensor:
            hol_state = self.hass.states.get(self._holiday_sensor)
            if hol_state:
                if "workday" in self._holiday_sensor and hol_state.state == "off":
                    is_holiday = True
                elif "workday" not in self._holiday_sensor and hol_state.state == "on":
                     is_holiday = True

        if is_holiday:
            return season_key, "light"

        zones = TIME_ZONES[time_key]
        load_level = "mid"
        
        if hour in zones["light"]:
            load_level = "light"
        elif hour in zones["max"]:
            load_level = "max"
        elif hour in zones["mid"]:
            load_level = "mid"

        if weekday == 5 and load_level == "max":
            load_level = "mid"

        return season_key, load_level

    async def _handle_energy_change(self, event):
        new_state = event.data.get("new_state")
        if not new_state or new_state.state in (None, "unknown", "unavailable"):
            return

        try:
            current_energy = float(new_state.state)
        except ValueError:
            return

        if self._last_energy is None:
            self._last_energy = current_energy
            return

        diff = current_energy - self._last_energy
        if diff < 0 or diff < 0.001:
            self._last_energy = current_energy
            return

        self._last_energy = current_energy

        now = dt_util.now()
        season, load_level = self._determine_season_and_load(now)
        self._current_load_level = load_level

        rates, climate_fee, fuel_fee = self._get_current_rates()
        base_unit_price = rates[season][load_level]
        
        # 세금 승수 계산 (동적)
        tax_multiplier = self._get_tax_multiplier()
        
        # 최종 단가 = (기본단가 + 기후요금 + 연료비) * (1 + 부가세% + 기금%)
        final_unit_price = (base_unit_price + climate_fee + fuel_fee) * tax_multiplier
        
        self._current_price = final_unit_price

        self._state += (diff * final_unit_price)
        self.async_write_ha_state()