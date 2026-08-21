# NEOPLE Game Analytics

던전앤파이터와 사이퍼즈 오픈 API를 활용한 게임 데이터 분석 포트폴리오입니다.

## 분석 범위

- 던전앤파이터 60%
  - 캐릭터 성장: 명성 구간, 직업별 성장 분포, 타임라인 이벤트
  - 경매장 시세: 아이템별 거래가, 중앙값, 가격 변동성
- 사이퍼즈 40%
  - 전체 캐릭터 공식 랭킹: 승률·승리·킬·도움·경험치
  - 공식 통합 랭킹 상위 N명 표본: 매칭·아이템 성과
- 최종 시각화: Power BI

## 데이터 흐름

```text
Neople REST API
    -> Python 수집기
    -> data/raw JSON 원천 보관
    -> Python 정제
    -> data/processed CSV
    -> PostgreSQL 적재
    -> SQL 분석 View
    -> Power BI 모델·대시보드
```

API는 SQL을 직접 제공하지 않으므로, API 응답을 원천 데이터로 저장한 뒤 PostgreSQL 또는 Power BI에 적합한 형태로 정제합니다. 이 저장·정제·분석 과정을 포트폴리오의 핵심으로 보여줍니다.

## 빠른 시작

PowerShell 기준입니다.

```powershell
cd outputs/neople-game-analytics
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`.env.example`을 `.env`로 복사하고, `.env`의 `NEOPLE_API_KEY`에 본인의 API Key를 입력합니다.

```powershell
Copy-Item .env.example .env
# .env에 API Key 입력

docker compose up -d db
python -m src.collect --game all
python -m src.transform
python -m src.load_postgres --mode replace
```

처음 실행하거나 API 호출 규모를 확인하려면 실제 수집 전에 다음 명령을 사용할 수 있습니다.

```powershell
python -m src.collect --game all --dry-run
```

## API Key 보안

API Key는 이 채팅이나 GitHub에 올리지 않습니다. `.env`는 `.gitignore`에 등록되어 있으며, 공유가 필요한 경우 `.env.example`만 사용합니다.

네오플 API의 제공 범위·호출 제한·약관은 변경될 수 있으므로 공개 대시보드나 원천 데이터 배포 전 공식 문서를 확인합니다.

- 던파 API: https://developers.neople.co.kr/contents/apiDocs
- 사이퍼즈 API: https://developers.neople.co.kr/contents/apiDocs/cyphers
- 공통 가이드: https://developers.neople.co.kr/contents/guide/pages/all
- 이용 약관: https://developers.neople.co.kr/contents/policy

## PostgreSQL과 Power BI

`docker compose up -d db`로 로컬 PostgreSQL을 실행한 뒤, `src.load_postgres`가 `data/processed`의 CSV를 `neople` 스키마에 적재합니다. 적재가 완료되면 `sql/03_views.sql`의 분석용 View가 생성됩니다.

Power BI Desktop에서 `Get data > PostgreSQL database`를 선택해 다음 View를 불러옵니다.

- `neople.vw_dnf_job_growth`
- `neople.vw_dnf_auction_summary`
- `neople.vw_dnf_latest_character`
- `neople.vw_cyphers_character_winrate`
- `neople.vw_cyphers_character_ranking_summary`
- `neople.vw_cyphers_item_performance`

이제 갱신 순서는 다음과 같습니다.

```text
API 수집 -> transform -> PostgreSQL 적재 -> Power BI Refresh
```

Power BI `.pbix` 파일은 Power BI Desktop에서 위 View를 최초 연결한 뒤 저장합니다.

## Power BI 모델

Power BI에서는 `powerbi/model.md`의 View 연결 기준을 사용합니다. 분석용 측정값은 `powerbi/measures.dax`에 정리했습니다.

권장 페이지:

1. **Executive Summary**: 두 게임 수집 건수·분석 기간·데이터 품질
2. **던파 성장 분석**: 명성 분포, 직업별 중앙값, 타임라인 이벤트
3. **던파 경매장 분석**: 아이템별 거래가, 중앙값, 변동성
4. **사이퍼즈 캐릭터 분석**: 공식 랭킹의 승률·승리·킬·도움·경험치
5. **사이퍼즈 아이템 분석**: 통합 랭킹 상위 N명 표본의 캐릭터·아이템 조합과 성과

## 분석상 한계

- 던파 명성 검색은 API가 제공하는 조건과 표본 범위 안에서 해석합니다.
- 던파 경매장 시세는 제공되는 최근 거래 데이터 범위 안에서 분석합니다.
- 사이퍼즈 매칭 데이터는 조회 기간·갱신 주기 제한을 명시합니다.
- 사이퍼즈 공식 캐릭터 랭킹과 상위 랭커 매칭 표본을 모집단으로 구분합니다.
- 사이퍼즈 아이템 성과는 전체 유저가 아니라 자동 수집한 상위 랭커 표본에 대한 결과입니다.
- API 표본으로 전체 이용자 모집단이나 인과관계를 단정하지 않습니다.
