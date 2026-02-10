"""Constants for Korea EV Charger integration."""

DOMAIN = "korea_ev_charger"

# 기본 설정값
DEFAULT_RATES = {
    "low_voltage": {
        "base": 2390,
        "summer": {"light": 84.3, "mid": 172.0, "max": 259.2},
        "spring_fall": {"light": 85.4, "mid": 97.2, "max": 102.1},
        "winter": {"light": 107.4, "mid": 154.9, "max": 217.5},
    },
    "high_voltage": {
        "base": 2580,
        "summer": {"light": 79.2, "mid": 137.4, "max": 190.4},
        "spring_fall": {"light": 80.2, "mid": 91.0, "max": 94.9},
        "winter": {"light": 96.6, "mid": 127.7, "max": 165.5},
    }
}

DEFAULT_CONTRACT_POWER = 7.0
DEFAULT_SENSOR_NAME = "EV Charging Cost"

DEFAULT_CLIMATE_FEE = 9.0
DEFAULT_FUEL_FEE = 5.0
DEFAULT_VAT_RATE = 10.0
DEFAULT_FUND_RATE = 3.7

# 계절 구분 (한전 전기자동차 충전전력 기준)
# 여름: 7~8월, 봄가을: 3~6월 9~10월, 겨울: 11~2월
SEASONS = {
    "summer": [7, 8],
    "winter": [11, 12, 1, 2],
    "spring_fall": [3, 4, 5, 6, 9, 10]
}

# 시간대 구분 (한전 전기자동차 충전전력 기준)
# 경부하: 23:00~09:00 (연중 동일)
# 여름/봄가을 중간부하: 09:00~11:00, 12:00~13:00, 17:00~23:00
# 여름/봄가을 최대부하: 11:00~12:00, 13:00~17:00
# 겨울 중간부하: 09:00~10:00, 12:00~17:00, 20:00~22:00
# 겨울 최대부하: 10:00~12:00, 17:00~20:00, 22:00~23:00
TIME_ZONES = {
    "summer_spring_fall": {
        "light": [23, 0, 1, 2, 3, 4, 5, 6, 7, 8],
        "mid": [9, 10, 12, 17, 18, 19, 20, 21, 22],
        "max": [11, 13, 14, 15, 16]
    },
    "winter": {
        "light": [23, 0, 1, 2, 3, 4, 5, 6, 7, 8],
        "mid": [9, 12, 13, 14, 15, 16, 20, 21],
        "max": [10, 11, 17, 18, 19, 22]
    }
}