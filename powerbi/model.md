# Power BI 데이터 모델

PostgreSQL의 `neople` 스키마에서 다음 View를 가져옵니다.

```text
vw_dnf_latest_character
vw_dnf_job_growth
vw_dnf_auction_summary
vw_dnf_equipment_adoption
vw_cyphers_character_ranking_summary
vw_cyphers_character_winrate
vw_cyphers_character_positioning
vw_cyphers_item_performance
```

이번 포트폴리오의 핵심 집계 로직은 Power BI 시각화가 아니라 PostgreSQL View에 둡니다. Power BI는 분석 질문별로 증거를 배치하고, 사용자가 표본·기간·직업을 바꿔가며 결론을 검증하는 데 사용합니다.

## 연결 방법

1. PostgreSQL이 실행 중인지 확인합니다.
2. Power BI Desktop에서 `Get data > PostgreSQL database`를 선택합니다.
3. `.env`의 `POSTGRES_HOST`, `POSTGRES_DB`로 지정한 서버와 데이터베이스에 접속합니다.
4. Navigator에서 `neople` 스키마의 View를 선택합니다.
5. Import 모드로 불러온 뒤 `powerbi/measures.dax`의 측정값을 추가합니다.

## Power BI Service와 웹 임베드

1. 이 문서의 View를 사용해 Power BI Report를 제작합니다.
2. Power BI Service Workspace에 Report를 게시합니다.
3. Microsoft Entra 앱을 만들고 Power BI API 접근을 허용합니다.
4. Entra 앱을 해당 Workspace의 Member 이상으로 추가합니다.
5. `apps/api/app/main.py`가 Report 정보와 View용 Embed token을 발급합니다.
6. `apps/web/app.js`가 `powerbi-client`로 Report를 표시합니다.

Power BI Report와 Workspace가 아직 생성되지 않은 상태에서는 API가 정상적인 Embed token을 발급할 수 없습니다. `POWERBI_TENANT_ID`, `POWERBI_CLIENT_ID`, `POWERBI_CLIENT_SECRET`, `POWERBI_WORKSPACE_ID`, `POWERBI_REPORT_ID`를 Kubernetes Secret·ConfigMap으로 주입한 뒤 사용합니다.

## 분석 질문별 페이지 설계

### 1. 분석 개요

- 질문: 이번 데이터로 어디까지 말할 수 있는가?
- 보여줄 것: 수집 기간, 캐릭터·경기·거래 관측 수, 공식 랭킹과 상위 랭커 표본의 구분
- 결론 영역: API 표본으로 확인된 사실과 확인할 수 없는 사실을 분리

### 2. 던파 성장 — 직업별 성장 격차는 장비 채택 차이와 함께 나타나는가?

- View: `vw_dnf_job_growth`, `vw_dnf_equipment_adoption`
- 핵심 지표: 직업별 중앙 명성, 전체 중앙값 대비 격차, 명성 IQR, 장비 채택률
- 시각화: 직업별 명성 분포와 `채택률 → 중앙 명성` 산점도
- 해석: 상관관계로 관찰하되 장비가 성장을 일으켰다고 인과 해석하지 않음

### 3. 던파 경매장 — 고가 아이템은 가격도 불안정한가?

- View: `vw_dnf_auction_summary`
- 핵심 지표: 중앙 거래가, IQR, 가격 표준편차, 변동계수(CV), 거래 관측 수
- 시각화: X축 중앙 거래가, Y축 가격 CV, 점 크기 거래 관측 수인 2x2 포지셔닝
- 해석: `고가·고변동`, `고가·안정`, `저가·고변동`, `저가·안정`으로 아이템군을 분류

### 4. 사이퍼즈 캐릭터 — 공식 랭킹과 상위 랭커 표본의 성과는 일치하는가?

- View: `vw_cyphers_character_positioning`
- 공식 데이터: `official_best_rank`, `official_median_win_rate_value`
- 표본 데이터: `sample_win_rate_pct`, `sample_match_count`
- 시각화: 공식 승률 값과 상위 랭커 표본 승률의 산점도, 표본 수 10경기 미만 제외
- 해석: 두 지표가 어긋나는 캐릭터를 후속 검증 대상으로 제시

### 5. 사이퍼즈 아이템 — 특정 아이템 조합은 캐릭터 기준 승률보다 높은가?

- View: `vw_cyphers_item_performance`
- 핵심 지표: 조합 승률, 캐릭터 기준 승률 대비 차이, 경기 수, 신뢰 플래그
- 시각화: X축 경기 수, Y축 기준 대비 승률 차이, `usable(30+)`와 `caution(10~29)` 구분
- 해석: 표본 수가 충분한 양의 차이만 후속 테스트 후보로 제시

## 새로 고침 순서

```text
python -m src.collect --game all
python -m src.transform
python -m src.load_postgres --mode replace
Power BI > Refresh
```

## 분석가 포트폴리오 산출물

각 페이지는 `질문 → 지표 정의 → SQL View → 시각적 패턴 → 해석과 한계` 순서로 구성합니다. 단순히 차트를 나열하지 않고, 같은 질문을 SQL 쿼리로 재현할 수 있도록 `sql/02_analysis_queries.sql`에 검증 쿼리를 함께 둡니다.
