# ⚡ Korea EV Charger Cost (한국형 전기차 충전 요금 계산기)

한국전력(KEPCO)의 **전기차 전용 요금제(저압/고압)**를 완벽하게 구현한 Home Assistant 커스텀 통합구성요소입니다.  
단순 전력량 요금뿐만 아니라, **기본요금(계약전력 반영), 기후환경요금, 연료비조정단가, 부가세, 전력산업기반기금**까지 모두 포함하여 실제 청구서와 100원 단위 이내의 정확도를 제공합니다.

## ✨ 주요 기능

* **계절별/시간대별 요금(TOU) 완벽 적용**: 여름/봄·가을/겨울철 및 경부하/중간부하/최대부하 자동 전환.
* **정밀한 세금 계산**: 부가가치세(10%), 전력산업기반기금(3.7%) 자동 합산 (사용자 요율 변경 가능).
* **계약 전력 반영**: 계약 전력(예: 7kW)에 따른 기본요금 정확한 부과.
* **공휴일 처리**: `Workday` 센서와 연동하여 평일 공휴일(설날, 삼일절 등)을 경부하(최저 요금)로 자동 적용.
* **사용자 편의성**:
    * 설치 시 **센서 이름 사용자 정의** 가능 (예: Tesla Charging Cost).
    * **결제 기준일** 설정 (매월 해당 일자에 기본요금 자동 부과).
    * **한글 UI** 지원 (설정 화면 및 옵션).

---

## 📥 설치 방법

### HACS를 통한 설치 (권장)
1.  HACS > Integrations > 우측 상단 메뉴 > **Custom repositories** 선택.
2.  이 저장소 주소를 입력하고 카테고리를 `Integration`으로 선택.
3.  **Korea EV Charger Cost** 검색 및 설치.
4.  Home Assistant **재시작**.

### 수동 설치
1.  `custom_components/korea_ev_charger` 폴더를 Home Assistant의 `custom_components` 폴더 내에 복사합니다.
2.  Home Assistant **재시작**.

---

## ⚙️ 설정 방법 (Configuration)

1.  **설정 > 기기 및 서비스 > 통합구성요소 추가** 버튼 클릭.
2.  **Korea EV Charger** 검색.
3.  다음 정보를 입력합니다:
    * **센서 이름**: 생성될 센서의 이름을 지정합니다 (예: `Tesla Charging Cost`).
    * **충전기 전력량 센서**: 월커넥터 등 충전기의 누적 사용량(kWh) 센서를 선택합니다.
    * **계약 종별**: 저압(Low Voltage) 또는 고압(High Voltage) 선택.
    * **계약 전력 (kW)**: 한전 계약 전력을 입력합니다 (가정용 완속은 보통 `7`kW).
    * **결제 기준일**: 매월 기본요금이 부과될 날짜를 입력합니다 (예: `1`일 또는 `25`일).
    * **공휴일 센서**: `binary_sensor.workday_sensor`를 선택합니다 (공휴일 할인 적용을 위해 필수).

---

## 📊 요금 계산 로직

이 컴포넌트는 다음과 같은 공식으로 실시간 요금을 누적합니다.

```math
총 요금 = (기본요금 합계) + (전력량 요금 합계)
```
1. **기본요금 (매월 결제일 자정 부과)**
   * 계산식: `(기본단가 × 계약전력) × 1.137(세금)`
   * 매월 설정한 결제 기준일이 시작되는 자정(00:00:01)에 자동으로 합산됩니다.
   * 예시: 7kW 계약 시 약 19,000원(세후)이 매달 자동 부과.
2. **전력량 요금 (실시간 충전 시 부과)**
   * 계산식: `(시간대별 단가 + 기후환경요금 + 연료비조정단가) × 1.137(세금) × 사용량(kWh)`
   * 센서의 전력 사용량이 증가할 때마다 실시간 단가를 적용하여 계산합니다.

   **참고**: `1.137`은 부가세(1.1) + 전력기금(0.037)의 합산 승수이며, 설정에서 변경 가능합니다.

## 📈 Utility Meter 설정 (필수)

이 센서는 자동차 주행거리계(ODO)처럼 **계속 누적되는 값**(`total`)입니다.  
**"이번 달 청구 요금"**을 보려면 **유틸리티 미터(Utility Meter)** 도우미를 반드시 만들어야 합니다.

1.  **설정 > 기기 및 서비스 > 도우미 > 도우미 만들기 > 유틸리티 미터** 선택.
2.  **이름**: 예) `이번 달 전기차 요금`
3.  **입력 센서**: 위에서 만든 통합구성요소 센서 (예: `sensor.tesla_charging_cost`)
4.  **미터 초기화 주기**: `매월 (Monthly)`
5.  **미터 초기화 오프셋**: 결제일과 동일하게 설정 (예: 1일이면 `0`, 25일이면 `24`일 등)

이제 대시보드에는 **`sensor.이번_달_전기차_요금`**을 등록하여 사용하세요.

---

## 🔔 자동화 예시 (Telegram 리포트)

### 1. 매일 밤 일간 리포트
```yaml
alias: Report energy daily
description: "매일 밤 사용량 및 예상 요금 발송"
trigger:
  - platform: time
    at: "23:59:50"
action:
  - service: telegram_bot.send_message
    data:
      parse_mode: markdown
      message: |
        📊 *{{ now().month }}월 {{ now().day }}일 에너지 리포트*

        ⚡ *오늘의 전력*
        • 사용량: `{{ states('sensor.daily_energy') | float(0) | round(1) }}` kWh
        
        💰 *예상 청구서*
        • 이번달 요금: *{{ "{:,}".format(states('sensor.ev_charging_monthly_cost') | int(0)) }}* 원
```
(참고: `sensor.ev_charging_monthly_cost`는 위에서 만든 Utility Meter 센서 이름입니다.)

### 2. 매월 월간 요금 리포트
```yaml
alias: Report energy monthly
description: "매월 결제일 전날 리포트 발송"
trigger:
  - platform: time
    at: "23:59:50"
condition:
  - condition: template
    # 매월 말일 또는 결제일 하루 전으로 설정 (예: 결제일이 1일이면 말일)
    value_template: "{{ (now() + timedelta(days=1)).day == 1 }}"
action:
  - service: telegram_bot.send_message
    data:
      parse_mode: markdown
      message: |
        📊 *{{ now().month }}월 최종 청구서 (전기차)*
        
        💰 *총 청구 금액*
        • 합계: *{{ "{:,}".format(states('sensor.ev_charging_monthly_cost') | int(0)) }}* 원
        
        ⚡ *상세 내역*
        • 총 사용량: {{ states('sensor.monthly_vehicle_energy') | float(0) | round(1) }} kWh
```
---
###❓ 자주 묻는 질문 (FAQ)
**Q. 요금이 한전 고지서보다 비싸게 나와요.**
1. **공휴일 센서 확인**: `binary_sensor.workday_sensor`가 연결되어 있지 않으면, 평일 공휴일(신정, 성탄절 등) 낮 시간에 비싼 평일 요금이 적용됩니다.
2. **겨울철 오전 8시~9시**: 겨울철(11~2월) 오전 8시부터는 **중간부하** 요금이 적용되어 비쌉니다. 차량의 출발 예약(공조) 등이 8시 이후에 작동했는지 확인하세요.

**Q. 요금이 너무 적게 나와요.**
1. **계약 전력 확인**: 설정(Configure) 메뉴에서 **계약 전력(Contract Power)**이 `7`kW로 되어 있는지 확인하세요. 기본값이 `1`이면 기본요금이 1/7로 계산됩니다.

Q. 기후환경요금이나 세율이 바뀌었어요.

통합구성요소의 구성하기(Configure) 버튼을 누르면 기후환경요금, 연료비조정단가, 세율 등을 언제든지 수정할 수 있습니다.
---
### 📝 라이선스
MIT License