# 이전 계획 보관본

> 이 문서는 이전에 검토했던 Power BI Service 임베딩·운영형 아키텍처를 보존하기 위한 기록입니다. 현재 무료 포트폴리오 방향의 기준 문서는 [`../current/plan.md`](../current/plan.md)입니다.

## 목표

Neople API 데이터를 수집해 PostgreSQL에 적재하고, Power BI Service Report를 웹 애플리케이션에 안전하게 임베드하는 운영형 분석 서비스를 구축한다.

## 이전 아키텍처

```text
Neople API
  → Kubernetes Worker CronJob
  → PostgreSQL
  → Power BI Service Report
  → FastAPI Embed Token API
  → powerbi-client 웹 화면
```

## 주요 구성

- `src/collect.py`: 던파·사이퍼즈 API 수집
- `src/transform.py`: 원천 JSON을 분석용 CSV로 변환
- `src/load_postgres.py`: PostgreSQL 적재
- `sql/03_views.sql`: Power BI용 분석 View
- `apps/api/app/main.py`: Microsoft Entra Client Credentials 인증 및 Power BI Embed Token 발급
- `apps/web/`: `powerbi-client` 기반 Report 표시
- `Dockerfile.worker`, `Dockerfile.api`, `Dockerfile.web`: 컨테이너 이미지
- `deploy/k8s/`: Worker, API, Web, Ingress 배포 템플릿
- `.gitlab-ci.yml`: 테스트, 이미지 빌드·Push, GitOps 반영

## 필요한 외부 리소스

- 관리형 PostgreSQL
- Power BI Workspace와 Report
- Power BI Embedded 또는 Fabric Capacity
- Power BI Report 게시 권한을 가진 Power BI Pro 사용자
- Microsoft Entra App Registration
- Entra Client Secret 또는 인증서
- Kubernetes 클러스터
- 컨테이너 레지스트리와 GitLab CI/GitOps 환경

## 주요 환경변수

```env
NEOPLE_API_KEY=...
POSTGRES_HOST=...
POSTGRES_DB=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_SSLMODE=require

POWERBI_TENANT_ID=...
POWERBI_CLIENT_ID=...
POWERBI_CLIENT_SECRET=...
POWERBI_WORKSPACE_ID=...
POWERBI_REPORT_ID=...
```

## 이전 실행 흐름

```powershell
python -m src.collect --game all
python -m src.transform
python -m src.load_postgres --mode replace
```

그 후 Power BI Desktop에서 PostgreSQL View를 연결해 Report를 작성하고 Power BI Service Workspace에 게시한다. 웹 애플리케이션은 API에서 짧은 수명의 Embed Token을 받아 Report를 표시한다.

## 현재 계획으로 전환한 이유

- 운영 환경에서 Power BI Capacity 비용이 발생한다.
- PostgreSQL, Kubernetes, Entra, API 서버까지 필요해 포트폴리오 범위를 넘어선다.
- 무료 공개가 목표인 채용 포트폴리오에는 인프라보다 분석 질문, 지표 정의, 게임 맥락 해석이 더 중요하다.
- Power BI Embedded 무료 토큰은 개발 테스트용이며 운영용 대체 수단이 아니다.

이 계획의 코드는 삭제하지 않고 참고용으로 남길 수 있지만, 무료 공개 포트폴리오의 실행 경로로 사용하지 않는다.
