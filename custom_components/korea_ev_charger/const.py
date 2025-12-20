"""Constants for Korea EV Charger integration."""

DOMAIN = "korea_ev_charger"
# https://cyber.kepco.co.kr/ckepco/mobile/cy_bill/bill_info_01.html
# 기본 설정값 (저압 기준)
# 사용자가 옵션에서 변경 가능하도록 Config Flow에서 이 값을 Default로 사용
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

# 계절 정의
SEASONS = {
    "summer": [6, 7, 8],
    "winter": [11, 12, 1, 2],
    "spring_fall": [3, 4, 5, 9, 10]
}

# 시간대 정의
# 22:00~08:00 경부하 등
TIME_ZONES = {
    "summer_spring_fall": {
        "light": [22, 23, 0, 1, 2, 3, 4, 5, 6, 7],
        "mid": [8, 9, 10, 12, 18, 19, 20, 21],
        "max": [11, 13, 14, 15, 16, 17]
    },
    "winter": {
        "light": [22, 23, 0, 1, 2, 3, 4, 5, 6, 7],
        "mid": [8, 12, 13, 14, 15, 19, 20, 21],
        "max": [9, 10, 11, 16, 17, 18]
    }
}