# 웹 대시보드

`web/index.html`은 별도의 백엔드 없이 정적 호스팅에서 동작하는 분석 화면입니다. `src.web_export`가 Power BI와 같은 `data/processed/*.csv`를 읽어 `web/data/dashboard.json`을 만들고, 브라우저는 이 JSON을 시각화합니다.

## 로컬 실행

저장소 루트에서 실행합니다.

```powershell
python -m src.web_export
python -m http.server 8000 --directory web
```

브라우저에서 `http://localhost:8000`을 엽니다. 생성된 `dashboard.json`이 없으면 `data/demo.json`으로 화면을 미리 볼 수 있습니다.

## 웹 공개 방식

Power BI 결과를 웹으로 보여주는 방식은 세 가지입니다.

1. **Power BI Publish to web**: 가장 간단하지만 인증 없이 인터넷에 공개됩니다. 보고서뿐 아니라 기본 데이터가 공개될 수 있으므로 포트폴리오용 공개 데이터에만 사용합니다. [Microsoft Learn: Publish to web](https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-publish-to-web)
2. **Power BI secure embed**: 사내 포털 등에 로그인 기반으로 임베드합니다. 보고서 권한과 RLS를 유지하지만, 사용자의 Power BI 권한·라이선스가 필요합니다. [Microsoft Learn: Secure embed](https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-embed-secure)
3. **이 저장소의 정적 대시보드**: Power BI 결과를 웹 친화적인 JSON으로 내보내 GitHub Pages나 다른 정적 호스팅에 배포합니다. 라이선스 의존성이 낮고 포트폴리오 공개에 적합하지만, Power BI의 고급 탐색 기능은 별도로 구현해야 합니다.

현재 저장소에는 세 번째 방식을 구현해 두었습니다. 실제 JSON을 공개 저장소에 포함할 때는 플레이어 식별자, 닉네임, 원천 응답 등 공개 범위를 먼저 검토하세요.

## 실제 데이터 배포

`web/data/dashboard.json`은 `.gitignore`에 포함되어 있습니다. 개인 데이터가 실수로 커밋되는 것을 막기 위한 설정입니다. 공개하기로 결정한 요약 데이터만 별도 검토한 뒤 배포 대상에 포함하세요.
