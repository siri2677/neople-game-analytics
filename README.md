# NEOPLE Game Analytics

던전앤파이터와 사이퍼즈 오픈 API를 활용해 게임 지표를 수집·정제하고,
분석 질문에 답하는 무료 정적 포트폴리오입니다. 던파 60%, 사이퍼즈 40%의
분석 범위를 유지하며, Power BI는 분석 검증용으로 사용하고 공개 결과는 정적
웹 대시보드로 제공합니다.

## 분석 질문

| 게임 | 질문 | 핵심 지표 |
| --- | --- | --- |
| 던파 성장 | 직업별 성장 격차가 장비 채택 차이와 함께 나타나는가? | 명성 중앙값·IQR, 명성 구간, 장비 채택률 |
| 던파 경매장 | 고가 아이템은 가격도 불안정한가? | 중앙 거래가, IQR, 표준편차, 변동계수, 관측 수 |
| 사이퍼즈 캐릭터 | 공식 랭킹과 상위 표본의 성과는 일치하는가? | 경기 수, 승률, 평균 킬·도움 |
| 사이퍼즈 아이템 | 아이템 조합이 캐릭터 기준 승률보다 높은 성과를 보이는가? | 조합 승률, 기준 대비 차이, 최소 표본 경고 |

각 결과는 `분석 질문 → 데이터 → 처리 방법 → 결과 → 게임 맥락 → 한계` 순서로
읽을 수 있도록 구성합니다. 관찰된 상관관계를 인과관계로 해석하지 않습니다.

## 데이터 흐름

```text
Neople REST API
    -> src.collect
    -> data/raw/*.json                 # 로컬 원천 보관
    -> src.transform
    -> data/processed/*.csv            # Power BI·분석 공통 산출물
    -> src.web_export
    -> web/data/dashboard.json         # 공개 전 검토하는 집계 JSON
    -> web/index.html                  # 정적 대시보드
```

`data/raw`, `data/processed`, 실제 API Key, 개인 식별정보는 공개하지 않습니다.
웹은 API를 직접 호출하지 않고 검토가 끝난 JSON만 읽습니다.

## 빠른 시작

PowerShell 기준입니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`에는 게임별 API Key를 입력합니다.

```env
DNF_API_KEY=발급받은_던파_API_KEY
CYPHERS_API_KEY=발급받은_사이퍼즈_API_KEY
```

수집 전 호출 범위를 확인한 뒤 실행합니다.

```powershell
python -m src.collect --game all --dry-run
python -m src.collect --game all
python -m src.transform
python -m src.web_export
python -m http.server 8000 --directory web
```

브라우저에서 `http://localhost:8000`을 열면 됩니다. 실제 산출물이 없으면
`web/data/demo.json`이 표시되어 API Key 없이도 화면과 분석 구조를 확인할 수
있습니다.

## 웹 대시보드

`web/`은 Overview, 던파, 사이퍼즈 탭을 제공하는 순수 HTML·CSS·JavaScript
정적 사이트입니다.

- Overview: 수집 건수, 명성 중앙값, 승률, 데이터 품질 메모
- 던파: 명성 구간, 직업별 분포, 장비 채택, 경매장 가격·변동성, 타임라인
- 사이퍼즈: 캐릭터 승률·성과, 아이템 사용, 캐릭터 기준 대비 조합 성과
- 필터: 직업 검색, 경매장 정렬, 캐릭터 최소 경기, 충분한 표본만 보기

아이템 조합은 최소 10경기 미만이면 `표본 부족`으로 표시합니다. 사이퍼즈 결과는
전체 이용자 모집단이 아니라 공식 랭킹에서 수집한 상위 표본으로 해석합니다.

## Power BI Desktop 검증

Power BI Desktop에서 `data/processed/*.csv`를 불러와
[`powerbi/model.md`](powerbi/model.md)의 관계와
[`powerbi/measures.dax`](powerbi/measures.dax)의 측정값을 적용합니다.

Power BI Service, Power BI Embedded, Fabric Capacity, Microsoft Entra 토큰은
이번 무료 포트폴리오 실행 경로에 포함하지 않습니다. `.pbix` 파일은 저장소에
넣지 않으며, 공개 웹 결과는 정적 대시보드가 담당합니다.

## 테스트와 공개 전 점검

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src
node --check web\app.js
```

공개 전에는 다음을 확인합니다.

- API Key와 DB 비밀번호가 커밋·로그·웹 산출물에 없는가
- raw JSON과 식별자, 닉네임, 내부 ID가 공개 JSON에서 제거됐는가
- 표본 범위·수집 시각·최소 경기 수가 화면에 표시되는가
- SQL 쿼리와 웹 숫자가 같은 처리 결과를 사용하는가

## 무료 배포

`.github/workflows/pages.yml`은 `main`에 반영된 `web/` 디렉터리를 GitHub Pages로
배포합니다. 저장소의 현재 원격이 GitLab이라면 GitHub 저장소로 미러링한 뒤 Pages
source를 GitHub Actions로 선택해야 합니다. 실제 데이터 JSON은 `.gitignore`에
남겨두고, 공개하기로 결정한 집계 파일만 별도 검토 후 배포합니다.

## API 문서와 한계

Neople API 제공 범위와 호출 제한은 변경될 수 있으므로 수집·공개 전에 공식 문서를
확인합니다.

- [던전앤파이터 API](https://developers.neople.co.kr/contents/apiDocs)
- [사이퍼즈 API](https://developers.neople.co.kr/contents/apiDocs/cyphers)
- [공통 가이드](https://developers.neople.co.kr/contents/guide/pages/all)

API 표본만으로 전체 이용자 모집단, 장비 효과, 아이템 효과 또는 인과관계를
단정하지 않습니다.
