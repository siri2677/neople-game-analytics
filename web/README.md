# 정적 웹 대시보드

`web/`은 별도 백엔드나 로그인 없이 동작하는 정적 분석 화면입니다. Python
`src.web_export`가 처리된 CSV를 읽어 `web/data/dashboard.json`을 만들고, 브라우저는
이 JSON만 읽습니다. API Key는 브라우저로 전달되지 않습니다.

## 로컬 실행

저장소 루트에서 실행합니다.

```powershell
python -m src.web_export
python -m http.server 8000 --directory web
```

브라우저에서 `http://localhost:8000`을 엽니다. 실제 데이터 JSON이 없으면
검토 가능한 데모 데이터가 표시됩니다.

## 화면 구성

- **Overview**: 수집 캐릭터·경기 수, 명성 중앙값, 승률, 데이터 품질
- **던파**: 명성 구간, 직업별 중앙값·IQR, 장비 채택률, 경매장 중앙값·IQR·CV,
  타임라인 이벤트
- **사이퍼즈**: 캐릭터별 경기 수·승률·킬·도움, 아이템 관측, 캐릭터 기준 대비
  아이템 조합 승률 차이

화면의 각 숫자는 표본 수와 함께 해석합니다. 사이퍼즈 아이템 조합은 최소 10경기
미만이면 표본 부족으로 표시되며, 표본이 충분한 결과만 후보 인사이트로 봅니다.

## 공개 원칙

`web/data/dashboard.json`은 `.gitignore`에 포함되어 있습니다. 공개하기로 결정한
집계 파일만 식별자와 원천 응답을 제거했는지 검토한 뒤 배포합니다.

- 닉네임, Player ID, 캐릭터 ID, 아이템 ID를 공개 산출물에 넣지 않습니다.
- 원천 JSON과 처리 중간 산출물을 정적 호스팅에 올리지 않습니다.
- 승률·가격은 기술통계이며 인과관계를 의미하지 않습니다.

## 배포

저장소 루트의 `.github/workflows/pages.yml`이 `web/`을 GitHub Pages로 배포합니다.
현재 저장소 원격이 GitLab인 경우에는 GitHub 저장소로 미러링한 뒤 Pages source를
GitHub Actions로 선택합니다. Power BI Service, Embed Token, PostgreSQL은 정적 웹
실행에 필요하지 않습니다.
