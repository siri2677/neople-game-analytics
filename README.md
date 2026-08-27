# NEOPLE Game Analytics

던전앤파이터와 사이퍼즈 오픈 API를 활용한 게임 데이터 분석 포트폴리오입니다.

## 분석 범위

- 던전앤파이터 60%
  - 캐릭터 성장: 명성 구간, 직업별 성장 분포, 타임라인 이벤트
  - 경매장 시세: 아이템별 거래가, 중앙값, 가격 변동성
- 사이퍼즈 40%
  - 캐릭터별 승률·승리·킬·도움
  - 매칭 상세 정보에서 확인 가능한 아이템 사용 패턴
- 최종 시각화: Power BI + 정적 웹 대시보드

## 데이터 흐름

```text
Neople REST API
    -> Python 수집기
    -> data/raw JSON 원천 보관
    -> Python 정제
    -> data/processed CSV
    -> Power BI 모델·대시보드
```

API는 SQL을 직접 제공하지 않으므로, API 응답을 원천 데이터로 저장한 뒤 PostgreSQL 또는 Power BI에 적합한 형태로 정제합니다. 이 저장·정제·분석 과정을 포트폴리오의 핵심으로 보여줍니다.

## 빠른 시작

PowerShell 기준입니다.

```powershell
cd neople-game-analytics
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`에 API Key와 수집 대상을 설정합니다. API Key는 실제 값을 입력하되 이 채팅이나 GitHub에 올리지 않습니다.

```env
NEOPLE_API_KEY=발급받은_네오플_API_KEY

DNF_SERVERS=all
DNF_FAME_BANDS=50000:52000,52000:54000,54000:56000
DNF_SAMPLE_LIMIT=30
DNF_AUCTION_ITEM_LIMIT=30

# 닉네임 또는 Player ID 중 하나를 설정
CYPHERS_NICKNAMES=분석할_닉네임
CYPHERS_PLAYER_IDS=
CYPHERS_GAME_TYPE=rating
CYPHERS_MATCH_LIMIT=50
CYPHERS_MATCH_DETAIL_LIMIT=100
```

실제 수집 전에는 반드시 `--dry-run`으로 대상과 호출 규모를 확인합니다.

```powershell
python -m src.collect --game all --dry-run
python -m src.collect --game all
python -m src.transform
python -m src.web_export
```

웹 화면은 별도의 정적 서버로 실행합니다.

```powershell
python -m http.server 8000 --directory web
```

브라우저에서 `http://localhost:8000`을 열면 됩니다. 실제 데이터로 생성한 `web/data/dashboard.json`이 없으면 포함된 데모 데이터가 표시됩니다.

## 현재 구현 상태

### 완료된 부분

- Neople API 수집기와 `.env` 기반 설정
- 원천 JSON 보관 및 CSV 변환 파이프라인
- 재수집 시 원천 파일이 덮어써지지 않도록 보존 처리
- 던파 서버 ID·캐릭터 ID 조인 정합성 개선
- 사이퍼즈 `matchId`·`match_id` 응답 형식 지원
- PostgreSQL 스키마와 Power BI 모델 문서
- Power BI와 같은 CSV를 사용하는 정적 웹 대시보드
- 웹 대시보드용 `src.web_export` JSON 생성기
- 자동 테스트 5개 통과

### 아직 직접 완료해야 하는 부분

- 실제 Neople API Key를 넣고 라이브 수집 실행
- Power BI Desktop에서 CSV를 불러오고 관계·측정값 설정
- Power BI 보고서(`.pbix`) 작성 및 Power BI Service 게시
- 공개 또는 로그인 기반 웹 배포 방식 결정

따라서 현재 저장소는 실행 가능한 분석 파이프라인과 웹 대시보드까지 준비된 상태이지만, 실제 API 데이터와 `.pbix` 보고서가 자동으로 완성된 상태는 아닙니다. API Key 없이 검증한 테스트는 코드 수준의 테스트와 `dry-run`이며, 실제 API 응답 검증은 사용자의 Key와 수집 대상 설정 후 진행해야 합니다.

## API Key 보안

API Key는 이 채팅이나 GitHub에 올리지 않습니다. `.env`는 `.gitignore`에 등록되어 있으며, 공유가 필요한 경우 `.env.example`만 사용합니다.

현재 방식에서 필요한 시크릿과 사용하지 않는 이전 설정은 [`docs/current/secret-config.md`](docs/current/secret-config.md)에 정리했습니다.

네오플 API의 제공 범위·호출 제한·약관은 변경될 수 있으므로 공개 대시보드나 원천 데이터 배포 전 공식 문서를 확인합니다.

- 던파 API: https://developers.neople.co.kr/contents/apiDocs
- 사이퍼즈 API: https://developers.neople.co.kr/contents/apiDocs/cyphers
- 공통 가이드: https://developers.neople.co.kr/contents/guide/pages/all
- 이용 약관: https://developers.neople.co.kr/contents/policy

## Power BI 모델

Power BI에서는 `powerbi/model.md`의 스타 스키마를 기준으로 CSV를 불러옵니다. 분석용 측정값은 `powerbi/measures.dax`에 정리했습니다.

### Power BI 보고서 생성 절차

1. `python -m src.transform` 실행 후 `data/processed/*.csv`를 Power BI Desktop에 불러옵니다.
2. [`powerbi/model.md`](powerbi/model.md)를 기준으로 날짜·캐릭터·경기 관계를 설정합니다.
3. [`powerbi/measures.dax`](powerbi/measures.dax)의 측정값을 Power BI에 추가합니다.
4. Executive Summary, 던파 성장·경매장, 사이퍼즈 캐릭터·아이템 페이지를 구성합니다.
5. 완성한 `.pbix`를 Power BI Service에 게시합니다.

이 저장소에는 `.pbix` 파일을 포함하지 않습니다. 데이터가 공개 저장소에 올라갈 수 있으므로, 실제 CSV와 보고서는 공개 전 개인정보·식별자·원천 응답을 검토합니다.

### Power BI를 웹으로 공개하는 방법

- **Publish to web**: 가장 간단하지만 인증 없이 인터넷에 공개됩니다. 보고서와 기본 데이터가 공개될 수 있으므로 공개해도 되는 데이터에만 사용합니다. [Microsoft Learn: Publish to web](https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-publish-to-web)
- **Secure embed**: 로그인과 권한을 유지한 채 사내 포털이나 웹에 임베드합니다. 보고서 권한·RLS를 유지하지만 Power BI 권한과 라이선스가 필요합니다. [Microsoft Learn: Secure embed](https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-embed-secure)
- **정적 웹 대시보드**: 아래 `web/` 화면을 GitHub Pages, Netlify, Cloudflare Pages 등에 배포합니다. Power BI 라이선스 없이 사용할 수 있지만 Power BI의 고급 탐색 기능은 별도로 구현해야 합니다.

## 웹 대시보드

`web/index.html`은 `data/processed`에서 만든 웹용 JSON을 읽어 브라우저에서 바로 보여주는 정적 대시보드입니다. Power BI 라이선스 없이도 GitHub Pages, Netlify, Cloudflare Pages 등에 배포할 수 있습니다.

```powershell
python -m src.web_export
python -m http.server 8000 --directory web
```

실제 데이터가 생성된 `web/data/dashboard.json`이 없으면 화면 확인을 위해 포함된 데모 데이터를 사용합니다. 생성된 대시보드 데이터는 개인 또는 이용자 분석 데이터가 될 수 있으므로 공개 저장소에 올리기 전에 공개 범위를 확인합니다. 자세한 Power BI 공개/비공개 임베드 방식은 [`web/README.md`](web/README.md)를 참고합니다.

권장 페이지:

1. **Executive Summary**: 두 게임 수집 건수·분석 기간·데이터 품질
2. **던파 성장 분석**: 명성 분포, 직업별 중앙값, 타임라인 이벤트
3. **던파 경매장 분석**: 아이템별 거래가, 중앙값, 변동성
4. **사이퍼즈 캐릭터 분석**: 캐릭터별 경기 수, 승률, 킬·도움
5. **사이퍼즈 아이템 분석**: 캐릭터·아이템 조합과 성과

## 분석상 한계

- 던파 명성 검색은 API가 제공하는 조건과 표본 범위 안에서 해석합니다.
- 던파 경매장 시세는 제공되는 최근 거래 데이터 범위 안에서 분석합니다.
- 사이퍼즈 매칭 데이터는 조회 기간·갱신 주기 제한을 명시합니다.
- API 표본으로 전체 이용자 모집단이나 인과관계를 단정하지 않습니다.

