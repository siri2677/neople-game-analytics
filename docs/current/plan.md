# 무료형 NEOPLE Game Analytics 포트폴리오 계획

## 1. 방향

네오플 `[전략분석실] 데이터분석가` 공고의 요구사항을 보여주는 **무료 정적 웹 포트폴리오**를 만든다.

공고에서 보여줘야 할 역량은 다음과 같다.

- 게임 지표·유저 데이터 가공, 분석, 리포팅
- SQL·Python 기반 데이터 추출과 분석
- 효율적인 데이터 구조 설계
- 라이브 게임 맥락을 고려한 해석
- AI 도구·프레임워크를 분석 업무에 활용
- 기획자·개발자에게 데이터 기반 메시지 전달

Power BI는 분석 검증과 Report 제작에 사용하되, 웹 공개의 필수 인프라로 사용하지 않는다.

## 2. 최종 형식

```text
GitHub Repository
  ├─ README: 문제 정의·데이터 흐름·분석 결과·한계
  ├─ src/: API 수집·정제·웹 데이터 생성
  ├─ sql/: 검증용 SQL과 지표 정의
  ├─ powerbi/: Power BI Desktop 모델·DAX 참고자료
  └─ web/: 정적 웹 대시보드

GitHub Pages
  └─ 채용 담당자가 로그인 없이 확인하는 공개 URL
```

GitHub Pages는 공개 저장소에서 무료로 사용할 수 있다. 실제 데이터는 공개해도 되는 요약 데이터만 배포하고, API Key와 원천 JSON은 절대 웹에 포함하지 않는다.

지원서 첨부가 필요하면 웹 URL과 GitHub URL을 우선 제출하고, 보조 자료는 PDF 1개 또는 공고에서 안내한 OneDrive 링크로 제한한다. Google Drive 링크는 사용하지 않는다.

## 3. 무료 범위 제한

### 사용

- Python, pandas, pytest
- SQL 파일과 로컬 CSV/JSON
- HTML, CSS, Vanilla JavaScript
- 기존 `src/collect.py`, `src/transform.py`, `src/web_export.py`
- Power BI Desktop을 분석·검증용으로만 사용
- 공개 GitHub 저장소와 GitHub Pages

### 사용하지 않음

- Power BI Embedded 또는 Fabric Capacity
- Power BI Embed Token API와 Microsoft Entra 인증
- 관리형 PostgreSQL을 필수 인프라로 사용
- Kubernetes, Docker 운영 클러스터, GitLab CI/GitOps
- 웹 브라우저에서 Neople API 직접 호출
- 공개 웹에 API Key 또는 원천 플레이어 식별정보 노출
- Power BI의 모든 기능을 웹에서 복제

이 제한을 지키면 웹 공개 비용은 0원으로 유지할 수 있다. Power BI Report 자체를 공개 웹에 임베드하는 `Publish to web`은 인증 없이 데이터가 공개될 수 있고, Embed Code 생성에 Pro/PPU 조건이 붙을 수 있으므로 기본 경로로 선택하지 않는다.

## 4. 구현 범위

### 화면 구성: 단일 페이지 + 3개 탭

#### Overview

- 분석 질문과 데이터 흐름
- 수집 기간과 표본 수
- 던파·사이퍼즈 핵심 KPI
- 데이터 품질과 해석 한계

#### 던파

- 직업별 명성 중앙값·분포
- 명성 구간별 캐릭터 수
- 경매장 중앙 거래가·가격 변동성
- 장비 채택률과 명성의 관계

#### 사이퍼즈

- 공식 랭킹과 상위 표본의 비교
- 캐릭터별 경기 수·승률
- 평균 킬·도움
- 캐릭터별 아이템 성과

각 화면은 `분석 질문 → 데이터 → 처리 방법 → 결과 → 게임 맥락 해석 → 한계` 순서를 유지한다.

## 5. 데이터 흐름

```text
Neople REST API
  → data/raw/*.json                 (로컬 원천 보관)
  → src/transform.py
  → data/processed/*.csv            (Power BI·분석 공통 산출물)
  → src/web_export.py
  → web/data/dashboard.json         (공개 전 검토하는 요약 데이터)
  → GitHub Pages
```

Power BI Desktop은 `data/processed/*.csv`를 사용한다. 웹 화면은 `dashboard.json`을 사용하므로 Power BI Service와의 실시간 연결은 필요하지 않다.

## 6. 분석 질문

### 던파 성장

> 직업별 성장 격차는 장비 채택 차이와 함께 나타나는가?

- 지표: 중앙 명성, 평균 명성, IQR, 장비 채택률
- SQL 검증: `sql/02_analysis_queries.sql`
- 해석: 관찰된 상관관계만 제시하고 장비가 성장을 일으켰다고 단정하지 않는다.

### 던파 경매장

> 고가 아이템은 가격도 불안정한가?

- 지표: 중앙 거래가, 가격 IQR, 표준편차, 변동계수, 관측 수
- 시각화: 가격·변동성 2축 포지셔닝
- 해석: 표본 수가 적은 아이템은 별도 경고한다.

### 사이퍼즈 캐릭터

> 공식 랭킹과 상위 플레이어 표본의 성과는 일치하는가?

- 지표: 공식 랭킹 값, 표본 경기 수, 표본 승률, 평균 킬·도움
- 해석: 두 지표가 어긋나는 캐릭터를 후속 분석 대상으로 제시한다.

### 사이퍼즈 아이템

> 특정 아이템 조합은 캐릭터 기준 승률보다 높은 성과를 보이는가?

- 지표: 아이템 조합 경기 수, 조합 승률, 캐릭터 기준 승률 대비 차이
- 해석: 최소 표본 수 기준을 통과한 결과만 후보로 제시한다.

## 7. AI 활용 증거

AI를 별도 유료 API 서비스로 운영하지 않고, 분석 과정의 생산성과 검증 절차를 보여준다.

- AI로 분석 질문과 SQL 초안 생성
- 실제 스키마·데이터로 SQL 결과 검증
- AI가 만든 해석과 실제 관측값을 분리
- 최종 인사이트는 분석자가 게임 맥락과 표본 한계를 검토해 작성
- README 또는 별도 문서에 `프롬프트 → 초안 → 검증 → 수정` 예시를 1개 이상 공개

AI가 생성한 문장을 그대로 결론으로 사용하지 않으며, 데이터에 없는 사실을 만들어내지 않는다.

## 8. 단계별 작업 계획

### 단계 1 — 기준선 확정

- `feature/neople-web-dashboard`를 무료형 포트폴리오 기준 브랜치로 사용
- `feat/postgres-powerbi-pipeline`의 운영형 임베딩 경로는 참고·보관만 함
- 분석 질문, 표본 범위, 공개 데이터 정책 확정

### 단계 2 — 데이터 계약과 재현성

- 각 CSV의 컬럼과 타입을 문서화
- 수집 시각, 표본 수, API 호출 범위를 화면에 표시
- raw JSON은 로컬에서만 보관
- 웹 배포용 JSON은 집계·비식별 요약 데이터만 포함
- API Key가 프론트엔드에 들어가지 않는지 검사

### 단계 3 — 분석 산출물 확장

- 던파 성장·경매장 지표를 웹 JSON에 포함
- 사이퍼즈 캐릭터·아이템 지표를 웹 JSON에 포함
- 표본 수 부족 경고와 데이터 품질 상태 추가
- SQL 결과와 웹 숫자가 일치하는지 테스트

### 단계 4 — 웹 대시보드 완성

- Overview, 던파, 사이퍼즈 3개 탭 구현
- 직업·캐릭터·아이템 필터는 정적 데이터 범위에서 구현
- 모바일 화면과 키보드 탐색 지원
- 차트마다 단위·표본 수·업데이트 날짜 표시
- 데모 데이터로 API Key 없이도 화면 확인 가능하게 유지

### 단계 5 — 채용 포트폴리오 문서화

- README 첫 화면에 문제 정의와 결과 요약 배치
- 각 분석 질문에 결론 2~3문장 작성
- 데이터 구조와 SQL 검증 방법 설명
- AI 활용 사례 1개 기록
- 분석 한계와 공개 데이터 주의사항 명시

### 단계 6 — 검증과 무료 배포

- `pytest` 통과
- Python compile 검사 통과
- JavaScript 문법 검사 통과
- 새 clone에서 데모 웹 화면 확인
- 실제 공개 전 `dashboard.json`의 식별자·원천 응답·비밀값 검사
- GitHub Pages로 `web/` 배포
- README에 공개 URL과 실행 방법 연결

## 9. 완료 기준

- [x] `.env.example`만으로 사용자가 설정 방법을 이해할 수 있다.
- [x] 실제 API Key는 GitHub·웹·프론트엔드에 노출되지 않는다.
- [x] API 없이도 데모 데이터로 웹 화면이 열린다.
- [x] 실제 수집 데이터로 `transform → web_export`가 재현된다.
- [x] Overview·던파·사이퍼즈 탭에서 공고와 연결되는 분석 결과를 보여준다.
- [x] 각 결과에 표본 범위와 한계가 표시된다.
- [x] Power BI Desktop에서 동일 CSV를 재검증할 수 있다.
- [x] 외부 유료 Capacity, DB, 인증 서버 없이 공개 URL을 운영할 수 있다.
- [ ] GitHub Pages 공개 URL과 README가 채용 담당자 관점에서 3분 안에 핵심을 전달한다.

## 10. 최종 의사결정

무료 포트폴리오의 최종 구조는 다음으로 고정한다.

```text
Power BI Desktop = 분석 검증용
GitHub README    = 분석 과정·기술 설명
GitHub Pages     = 공개 웹 결과물
```

Power BI Service Embedded는 비용·인프라·보안 범위가 커서 이번 포트폴리오의 필수 범위에서 제외한다.
