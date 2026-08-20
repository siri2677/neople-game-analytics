# Power BI 데이터 모델

## 권장 관계

Power BI에서 각 CSV를 불러온 뒤 다음 관계를 설정합니다.

```text
dim_date[Date]
  1 ─── * dnf_character_snapshot[snapshot_date_date]
  1 ─── * dnf_auction_sold[sold_date_date]
  1 ─── * cyphers_match[match_date_date]

dnf_character_snapshot[character_id]
  1 ─── * dnf_equipment[character_id]
  1 ─── * dnf_timeline[character_id]

cyphers_player_match_performance[match_id]
  1 ─── * cyphers_match_item[match_id]
```

실제 Power BI에서는 날짜와 시간의 granularities가 다르므로 Power Query에서 다음 보조 열을 생성합니다.

- `snapshot_date_date = Date.From([snapshot_date])`
- `sold_date_date = Date.From([sold_date])`
- `match_date_date = Date.From([match_date])`

## 페이지별 시각화

### 1. Executive Summary

- 카드: 수집 캐릭터 수, 경기 수, 아이템 수, 분석 기간
- 막대그래프: 게임별 데이터 건수
- 주의사항 텍스트: 표본 범위·API 갱신 시점·데이터 누락

### 2. DNF 성장

- 명성 구간별 캐릭터 수: Column chart
- 직업별 명성 중앙값: Bar chart
- 날짜별 평균 명성: Line chart
- 직업·서버·명성 구간: Slicer

### 3. DNF 경매장

- 아이템별 중앙 거래가: Bar chart
- 거래가 분포: Box plot 또는 Scatter chart
- 거래 관측 수와 가격 변동성: Scatter chart
- 아이템명·기간: Slicer

### 4. Cyphers 캐릭터

- 캐릭터별 승률: Bar chart
- 경기 수 대비 승률: Scatter chart
- 평균 킬·도움: Matrix
- 공식전·일반전: Legend 또는 Slicer

### 5. Cyphers 아이템

- 캐릭터별 아이템 채택률: Matrix
- 아이템별 승률: Bar chart
- 최소 표본 수 10경기 필터

