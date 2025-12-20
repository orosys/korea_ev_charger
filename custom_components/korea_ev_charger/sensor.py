"""Sensor platform for Korea EV Charger."""
import calendar
# datetime은 타입 힌트용으로만 남기고, 실제 시간은 dt_util 사용
from datetime import datetime
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
# Home Assistant 표준 시간대 유틸리티 임포트
import homeassistant.util.dt as dt_util
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, SEASONS, TIME_ZONES, DEFAULT_RATES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor."""
    source_sensor = config_entry.data["source_sensor"]
    voltage_type = config_entry.data.get("voltage_type", "low_voltage")
    holiday_sensor = config_entry.data.get("holiday_sensor")
    
    sensor = KoreaEVCostSensor(hass, source_sensor, voltage_type, holiday_sensor, config_entry)
    async_add_entities([sensor])

class KoreaEVCostSensor(RestoreEntity, SensorEntity):
    """Calculates cost based on TOU rates and daily base rate."""

    _attr_has_entity_name = True
    _attr_name = "EV Charging Cost"
    _attr_native_unit_of_measurement = "KRW"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, hass, source_entity, voltage_type, holiday_sensor, config_entry):
        """Initialize the sensor."""
        self.hass = hass
        self._source_entity = source_entity
        self._voltage_type = voltage_type
        self._holiday_sensor = holiday_sensor
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

        # 1. 전력 사용량 변화 감지
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._source_entity], self._handle_energy_change
            )
        )

        # 2. 매일 자정 기본요금 합산
        self.async_on_remove(
            async_track_time_change(
                self.hass, self._async_daily_base_rate_update, hour=0, minute=0, second=0
            )
        )

    async def _async_daily_base_rate_update(self, now):
        """Add daily prorated base rate at midnight."""
        base_rate = DEFAULT_RATES[self._voltage_type]["base"]
        
        _, days_in_month = calendar.monthrange(now.year, now.month)
        
        daily_base = base_rate / days_in_month
        
        self._state += daily_base
        _LOGGER.debug("Daily base rate added: %f KRW", daily_base)
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        return {
            "current_price_per_kwh": self._current_price,
            "load_level": self._current_load_level,
            "season": self._current_season,
            "source_sensor": self._source_entity,
            "base_rate_type": self._voltage_type
        }

    @property
    def native_value(self):
        """Return the total calculated cost rounded to 2 decimal places."""
        return round(self._state, 2)

    def _get_current_rates(self):
        defaults = DEFAULT_RATES[self._voltage_type]
        opts = self._config_entry.options
        
        return {
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

        rates = self._get_current_rates()
        price = rates[season][load_level]
        self._current_price = price

        self._state += (diff * price)
        self.async_write_ha_state()