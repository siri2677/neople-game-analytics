# Power BI 데이터 모델

PostgreSQL의 `neople` 스키마에서 다음 View를 가져옵니다.

```text
vw_dnf_latest_character
vw_dnf_job_growth
vw_dnf_auction_summary
vw_dnf_equipment_adoption
vw_cyphers_character_ranking_summary
vw_cyphers_character_winrate
vw_cyphers_item_performance
```

이번 포트폴리오의 핵심 집계 로직은 Power BI 시각화가 아니라 PostgreSQL View에 둡니다. Power BI는 필터·카드·차트 표현과 탐색에 집중합니다.

## 연결 방법

1. PostgreSQL이 실행 중인지 확인합니다.
2. Power BI Desktop에서 `Get data > PostgreSQL database`를 선택합니다.
3. Server는 `localhost`, Database는 `neople`을 입력합니다.
4. Navigator에서 `neople` 스키마의 View를 선택합니다.
5. Import 모드로 불러온 뒤 `powerbi/measures.dax`의 측정값을 추가합니다.

## 페이지별 View와 시각화

### Executive Summary

- `vw_dnf_latest_character`: 캐릭터 수, 평균 명성
- `vw_cyphers_character_winrate`: 전체 경기 수, 평균 승률
- `vw_dnf_auction_summary`: 아이템 거래 관측 수

### DNF 성장

- View: `vw_dnf_job_growth`
- 직업별 캐릭터 수: Column chart
- 직업별 중앙 명성: Bar chart
- 최소·최대 명성: Tooltip 또는 Table

### DNF 경매장

- View: `vw_dnf_auction_summary`
- 아이템별 중앙 거래가: Bar chart
- 거래 관측 수와 가격 변동성: Scatter chart
- 거래 기간: Slicer

### DNF 장비

- View: `vw_dnf_equipment_adoption`
- 직업별 아이템 채택률: Matrix
- 채택 캐릭터 수: Bar chart

### 사이퍼즈 캐릭터

- 공식 전체 랭킹 View: `vw_cyphers_character_ranking_summary`
- `ranking_type`을 기준으로 승률·승리·킬·도움·경험치 비교
- `best_rank`, `median_ranking_value`, `max_ranking_value` 사용
- 표본 기반 성과 View: `vw_cyphers_character_winrate`
- 표본 경기 수 대비 승률: Scatter chart

### 사이퍼즈 아이템

- View: `vw_cyphers_item_performance`
- 캐릭터·아이템 조합별 승률: Matrix
- 공식 통합 랭킹 상위 N명 표본이라는 설명을 함께 표시합니다.
- 표본 경기 수가 적은 조합은 필터링합니다.

## 새로 고침 순서

```text
python -m src.collect --game all
python -m src.transform
python -m src.load_postgres --mode replace
Power BI > Refresh
```
