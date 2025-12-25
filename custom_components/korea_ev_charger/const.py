"""Constants for Korea EV Charger integration."""

DOMAIN = "korea_ev_charger"

# 기본 설정값 (저압 기준)
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

# 추가 요금 기본값 (2025년 기준)
DEFAULT_CLIMATE_FEE = 9.0  # 기후환경요금
DEFAULT_FUEL_FEE = 5.0     # 연료비조정단가

# 세금 및 기금 기본값 (%)
DEFAULT_VAT_RATE = 10.0    # 부가가치세 (10%)
DEFAULT_FUND_RATE = 3.7    # 전력산업기반기금 (3.7%)

# 계절 및 시간대 정의
SEASONS = {
    "summer": [6, 7, 8],
    "winter": [11, 12, 1, 2],
    "spring_fall": [3, 4, 5, 9, 10]
}

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