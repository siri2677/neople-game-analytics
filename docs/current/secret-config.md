# 현재 방식의 시크릿·환경변수 설정

## 기준

현재 포트폴리오는 Power BI Embedded, Microsoft Entra, 관리형 PostgreSQL, Kubernetes 없이 **Python 수집기와 정적 웹 대시보드**로 운영한다.

따라서 웹사이트를 보여주기 위한 서버 시크릿은 필요하지 않다. API Key는 데이터를 수집할 때만 로컬에서 사용하고, 웹 브라우저에는 전달하지 않는다. 던파와 사이퍼즈는 게임별 API Key를 각각 발급·사용해야 하므로 하나의 공통 Key 변수로 관리하지 않는다.

Neople 공통 응답 코드에도 다른 게임용 Key를 사용하면 `API005(해당 게임으로 발급되지 않은 API Key)`가 반환될 수 있다고 안내되어 있다. 따라서 발급받은 Key가 어느 게임용인지 확인한 뒤 해당 변수에 넣는다. [Neople API 공통 가이드](https://developers.neople.co.kr/contents/guide/pages/all)와 [응답 코드 문서](https://developers.neople.co.kr/contents/guide/pages/code)를 참고한다.

## 현재 사용 환경변수

### 시크릿: 반드시 로컬 `.env`에만 저장

| 변수 | 필수 | 용도 | 저장 위치 |
| --- | --- | --- | --- |
| `DNF_API_KEY` | 던파 수집 시 필수 | 던파 REST API 인증 | 로컬 `.env`만 |
| `CYPHERS_API_KEY` | 사이퍼즈 수집 시 필수 | 사이퍼즈 REST API 인증 | 로컬 `.env`만 |

`.env`는 `.gitignore`에 등록되어 있다. 실제 Key를 README, GitHub, HTML, JavaScript, `dashboard.json`에 작성하지 않는다.

### 일반 수집 설정: 시크릿 아님

| 변수 | 기본값 | 용도 |
| --- | --- | --- |
| `DNF_SERVERS` | `all` | 던파 서버 범위 |
| `DNF_FAME_BANDS` | `50000:52000,52000:54000,54000:56000` | 명성 검색 구간 |
| `DNF_SAMPLE_LIMIT` | `30` | 구간별 캐릭터 표본 수 |
| `DNF_AUCTION_ITEM_LIMIT` | `30` | 경매장 조회 아이템 수 |
| `CYPHERS_NICKNAMES` | 빈 값 | 사이퍼즈 닉네임 검색 대상 |
| `CYPHERS_PLAYER_IDS` | 빈 값 | 사이퍼즈 Player ID 대상 |
| `CYPHERS_GAME_TYPE` | `rating` | 공식전/일반전 구분 |
| `CYPHERS_START_DATE` | 최근 30일 자동 | 수집 시작 시각 |
| `CYPHERS_END_DATE` | 현재 시각 자동 | 수집 종료 시각 |
| `CYPHERS_MATCH_LIMIT` | `50` | 플레이어별 경기 수 |
| `CYPHERS_MATCH_DETAIL_LIMIT` | `100` | 상세 경기 수 |

실제 사용 가능한 전체 예시는 [`.env.example`](../../.env.example)에 있다.

## 현재 설정 예시

```env
DNF_API_KEY=replace_with_dnf_key
CYPHERS_API_KEY=replace_with_cyphers_key

DNF_SERVERS=all
DNF_FAME_BANDS=50000:52000,52000:54000,54000:56000
DNF_SAMPLE_LIMIT=30
DNF_AUCTION_ITEM_LIMIT=30

# 닉네임 또는 Player ID 중 하나를 설정
CYPHERS_NICKNAMES=
CYPHERS_PLAYER_IDS=
CYPHERS_GAME_TYPE=rating
CYPHERS_START_DATE=
CYPHERS_END_DATE=
CYPHERS_MATCH_LIMIT=50
CYPHERS_MATCH_DETAIL_LIMIT=100
```

## 더 이상 현재 방식에서 넣지 않는 값

이전 Power BI Service Embedded·운영형 계획에서 사용하던 아래 값은 현재 무료 정적 웹 대시보드의 실행에 필요하지 않다.

```env
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_SSLMODE
POWERBI_TENANT_ID
POWERBI_CLIENT_ID
POWERBI_CLIENT_SECRET
POWERBI_WORKSPACE_ID
POWERBI_REPORT_ID
POWERBI_API_BASE_URL
POWERBI_SCOPE
POWERBI_TOKEN_LIFETIME_MINUTES
CORS_ALLOW_ORIGINS
```

위 값이 들어 있는 예전 `.env`를 재사용하지 말고, 현재 브랜치의 `.env.example`을 기준으로 새 `.env`를 만든다. 이전 운영형 설정은 [`../lagacy/plan.md`](../lagacy/plan.md)에 보관되어 있다.

## 실행 시점별 시크릿 필요 여부

| 작업 | API Key 필요 여부 |
| --- | --- |
| 데모 웹 화면 보기 | 불필요 |
| `python -m src.transform` 실행 | 불필요 |
| `python -m src.web_export` 실행 | 불필요 |
| `python -m src.collect --game dnf` | `DNF_API_KEY` 필요 |
| `python -m src.collect --game cyphers` | `CYPHERS_API_KEY` 필요 |
| `python -m src.collect --game all` | 두 Key 모두 필요 |
| 생성된 정적 웹사이트 공개 | 불필요 |

즉, 필요한 게임의 데이터를 수집하고 정제·검토해 공개용 `dashboard.json`을 만든 후에는 웹사이트가 API Key 없이도 동작한다.

`web/data/dashboard.json`은 기본적으로 `.gitignore`에 들어 있다. 공개하기로 결정한 집계 데이터만 검토 후 배포 대상에 의도적으로 포함하거나, 배포 과정에서 안전한 공개용 파일로 복사한다. 검토하지 않은 원천 CSV·JSON을 강제로 커밋하지 않는다.

## 공개 전 점검

`dashboard.json`과 CSV는 시크릿은 아니지만 플레이어 닉네임, Player ID, 수집 시각 등 공개를 원하지 않는 정보가 포함될 수 있다.

- `data/raw` 원천 JSON은 공개하지 않는다.
- 실제 공개용 JSON은 필요한 집계값만 남긴다.
- 닉네임·Player ID·내부 경로를 공개할지 검토한다.
- API Key가 파일에 들어갔는지 검색한다.

```powershell
rg -n "DNF_API_KEY|CYPHERS_API_KEY|POWERBI_CLIENT_SECRET|POSTGRES_PASSWORD|replace_with_.*secret" . -g '!*.pyc' -g '!data/raw/**'
git status --short
```

GitHub Actions로 자동 수집을 추가하는 경우에도 `DNF_API_KEY`와 `CYPHERS_API_KEY`는 GitHub Actions Secret으로만 주입하고, 웹 산출물이나 로그에 출력하지 않는다. 현재 계획에는 자동 수집 배포를 필수로 포함하지 않는다.

## 무료 공개 운영 원칙

```text
DNF_API_KEY   = 던파 로컬 수집 단계에서만 사용
CYPHERS_API_KEY = 사이퍼즈 로컬 수집 단계에서만 사용
CSV/JSON      = 공개 전 비식별·집계 검토
웹 브라우저   = 정적 JSON만 읽음
Power BI      = 선택적 검증 도구
Power BI API  = 사용하지 않음
```
