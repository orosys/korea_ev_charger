"""Sensor platform for Korea EV Charger."""
from datetime import datetime
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)

from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.event import async_track_state_change_event
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
    """Calculates cost based on TOU rates."""

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
        
        # 속성값
        self._current_price = 0
        self._current_load_level = "Unknown"
        self._current_season = "Unknown"

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        
        # 상태 복원 (재부팅 시 값 유지)
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            try:
                self._state = float(last_state.state)
            except ValueError:
                self._state = 0.0

        # 소스 센서 변화 감지
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._source_entity], self._handle_energy_change
            )
        )

    @property
    def extra_state_attributes(self):
        """Return details about the current calculation."""
        return {
            "current_price_per_kwh": self._current_price,
            "load_level": self._current_load_level, # 경부하/중간부하/최대부하
            "season": self._current_season,
            "source_sensor": self._source_entity
        }

    @property
    def native_value(self):
        """Return the total calculated cost."""
        return self._state

    def _get_current_rates(self):
        """Get rates from options or defaults."""
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
        """Determine current season and load level based on KEPCO tables."""
        month = now.month
        hour = now.hour
        weekday = now.weekday() # 0=Mon, 5=Sat, 6=Sun
        
        # 1. 계절 판단
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

        # 2. 공휴일/일요일 체크 (공휴일이면 전 시간 경부하)
        is_holiday = False
        if weekday == 6: # 일요일은 무조건 휴일
            is_holiday = True
        elif self._holiday_sensor:
            # holiday_sensor 상태 확인
            hol_state = self.hass.states.get(self._holiday_sensor)
            
            if hol_state:
                # Workday 센서는 'off'가 휴일(비근무일)입니다.
                if "workday" in self._holiday_sensor and hol_state.state == "off":
                    is_holiday = True
                # 일반적인 공휴일 센서가 'on'일 때 공휴일이라면 아래 조건 사용
                # 사용자가 헷갈릴 수 있으니, 센서가 'on'이거나 'off'인 경우 모두 고려하여
                # workday 센서가 아니면 'on'을 휴일로 간주하는 로직 예시:
                elif "workday" not in self._holiday_sensor and hol_state.state == "on":
                     is_holiday = True

        if is_holiday:
            return season_key, "light"

        # 3. 시간대별 부하 판단
        zones = TIME_ZONES[time_key]
        load_level = "mid" # default fallback
        
        if hour in zones["light"]:
            load_level = "light"
        elif hour in zones["max"]:
            load_level = "max"
        elif hour in zones["mid"]:
            load_level = "mid"

        # 4. 토요일 예외 처리 (이미지 참조: 최대부하 -> 중간부하)
        if weekday == 5 and load_level == "max":
            load_level = "mid"

        return season_key, load_level

    async def _handle_energy_change(self, event):
        """Handle updates from the energy sensor."""
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")

        if not new_state or new_state.state in (None, "unknown", "unavailable"):
            return

        try:
            current_energy = float(new_state.state)
        except ValueError:
            return

        # 이전 값이 없으면 초기화만 하고 리턴 (계산 불가)
        if self._last_energy is None:
            self._last_energy = current_energy
            return

        # 에너지 차이 계산
        diff = current_energy - self._last_energy
        
        # 값이 튀거나 리셋된 경우(음수) 무시 혹은 0부터 다시 시작
        if diff < 0:
             # 충전기 센서가 리셋되었다면, 이번 틱은 무시하고 last_energy만 업데이트
            self._last_energy = current_energy
            return
            
        # 0.001 kWh 미만의 미세 변동은 무시 (노이즈 방지)
        if diff < 0.001:
            return 

        self._last_energy = current_energy

        # 현재 시간 기준 요금 계산
        now = datetime.now()
        season, load_level = self._determine_season_and_load(now)
        self._current_load_level = load_level

        rates = self._get_current_rates()
        price = rates[season][load_level]
        self._current_price = price

        # 비용 누적
        added_cost = diff * price
        self._state += added_cost
        
        self.async_write_ha_state()