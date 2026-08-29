# 현재 방식의 CI/CD와 GitOps

## 목적

현재 분석 방식은 Power BI Embedded나 PostgreSQL API가 아니라 **정제된 대시보드 JSON을 제공하는 읽기 전용 API와 정적 Web 화면**이다.

따라서 컨테이너를 다음 두 개로 나눈다.

| 이미지 | 역할 |
| --- | --- |
| `api` | 검토된 `dashboard.json`을 `/api/dashboard`로 제공하고 `/healthz` 응답. 동일 이미지를 Worker CronJob도 사용 |
| `web` | Nginx로 HTML·CSS·JavaScript를 제공하고 `/api/dashboard`를 API에 프록시 |

API 컨테이너는 요청을 처리할 때 Neople API를 직접 호출하지 않으며 API Key를 포함하지 않는다. 같은 API 이미지를 사용하는 Worker CronJob이 Secret으로 주입된 Key를 사용해 수집·정제·공개 JSON 생성을 실행한다. 데이터가 없을 때 API 이미지에는 저장소의 데모 JSON이 포함된다.

## Atmo와 동일한 배포 흐름

```text
feature 브랜치
  → Python 테스트·compile 검사

main 브랜치
  → Python 테스트·compile 검사
  → API(Worker 겸용)/Web Docker 이미지 한 번 빌드·Push (전체 커밋 SHA)
  → GitOps 저장소 dev API/Web newTag 변경
  → Argo CD 또는 Flux 동기화

vMAJOR.MINOR.PATCH 태그
  → main 커밋의 SHA 이미지 존재 여부 확인
  → API/Web에 버전 태그만 추가 (재빌드하지 않음)
  → GitOps 저장소 prod API/Web newTag 변경
  → Argo CD 또는 Flux 동기화
```

API(Worker 겸용)와 Web은 두 이미지 모두 동일한 커밋 기준의 전체 SHA 태그를 사용한다. 릴리스 버전 태그는 Registry에 이미 Push된 SHA 이미지의 매니페스트를 가리키는 별칭이다.

- `main` 브랜치: `$CI_COMMIT_SHA`
- SemVer Git tag: `$CI_COMMIT_TAG`를 기존 `$CI_COMMIT_SHA` 이미지에 추가
- Feature 브랜치: 테스트만 실행하며 이미지·GitOps 배포를 만들지 않음

릴리스 Job은 `docker buildx imagetools create`로 API/Web의 버전 태그를 추가한다. 이 명령은 기존 Registry 매니페스트를 재사용하므로 Dockerfile을 다시 빌드하지 않는다. 릴리스 전후 매니페스트 Digest가 같은지도 확인한다. GitOps 커밋에는 `[skip ci]`를 넣어 GitOps 저장소의 검증 파이프라인이 불필요하게 반복되지 않게 한다.

## 저장소 파일

- [`.gitlab-ci.yml`](../../.gitlab-ci.yml): 테스트, API/Web 이미지 빌드·Push, GitOps 태그 변경
- [`Dockerfile.api`](../../Dockerfile.api): FastAPI API·Worker 공용 이미지
- [`Dockerfile.web`](../../Dockerfile.web): Nginx 정적 Web 이미지
- [`docker-compose.yml`](../../docker-compose.yml): API/Web 로컬 통합 실행 예시
- [`apps/api/main.py`](../../apps/api/main.py): 대시보드 JSON API
- [`deploy/nginx/web.conf`](../../deploy/nginx/web.conf): Web → API 프록시
- [`ci/update-gitops-tags.sh`](../../ci/update-gitops-tags.sh): API/Web `newTag` 동시 변경

## GitLab CI/CD 변수

GitLab Container Registry 관련 `CI_REGISTRY`, `CI_REGISTRY_IMAGE`, `CI_REGISTRY_USER`, `CI_REGISTRY_PASSWORD`는 GitLab 기본 제공 변수를 사용한다.

서비스 저장소의 GitOps 태그 변경 Job은 `lime985340` Group에서 다음 세 변수를
상속한다. 서비스 프로젝트에 같은 변수를 다시 만들지 않는다.

| 변수 | 용도 |
| --- | --- |
| `GITOPS_PUSH_TOKEN` | GitOps 저장소 Push 권한이 있는 토큰. Masked·Protected 권장 |
| `GITOPS_PUSH_TOKEN_USER` | 토큰에 대응하는 사용자명 |
| `GITOPS_BRANCH` | 현재 GitOps 대상 브랜치. `feature/clean-gitops-layout` 또는 `main` |

GitOps 저장소 주소와 앱 경로는 서비스마다 다르므로 `.gitlab-ci.yml`에 고정한다.
GitOps 대상 브랜치는 Atmo와 Neople 서비스가 공통으로 상속하는 `lime985340`
Group Variable `GITOPS_BRANCH` 하나로 관리한다.

```yaml
GITOPS_REPO_HOST_PATH: "gitlab.com/lime985340/gitops.git"
GITOPS_APP_PATH: "workloads/neople-game-analytics"
```

현재 `lime985340` Group Variable `GITOPS_BRANCH`는 `feature/clean-gitops-layout`을
가리킨다. GitOps 구조가 `main`으로 병합된 뒤 Group Variable 값만 `main`으로
변경한다. `GITOPS_ENVIRONMENT`는 사용자가 입력하지 않으며 CI가 `main → dev`,
릴리스 태그 `→ prod`로 자동 결정한다.

기존 `lime985340` Group Variable을 서비스 저장소와 `gitops` 저장소가 상속하고
있다면 Registry 인증, Sealed Secrets 인증서, GitOps Push 인증 변수는 새로 만들지
않는다. 이 애플리케이션 때문에 새로 추가할 값은 `gitops` 저장소의 Neople 전용
환경별 File Variable 2개뿐이다. 임의의 문자열이나 예시 Key를 넣으면 Worker 호출이
실패하므로 실제 발급값을 준비한 뒤 등록한다.

```text
NEOPLE_API_DEV_ENV
NEOPLE_API_PROD_ENV
```

각 File Variable의 내용은 다음과 같다.

```env
DNF_API_KEY=<실제 던파 API Key>
CYPHERS_API_KEY=<실제 사이퍼즈 API Key>
```

`GITOPS_PUSH_TOKEN`, `GITOPS_PUSH_TOKEN_USER`, `GITOPS_BRANCH`는 기존
`lime985340` Group Variable을 그대로 사용한다. `SEALED_SECRETS_CERT`,
`GITLAB_REGISTRY_USERNAME`, `GITLAB_REGISTRY_TOKEN`은 현재 `gitops` 프로젝트에
등록된 공통 GitOps 운영 변수다. 변수 상속과 프로젝트 범위가 의도한 상태인지
확인한다. 자세한 매핑은
[gitops Secret 변수 문서](https://gitlab.com/lime985340/gitops/-/raw/feature/clean-gitops-layout/docs/secret-variables.md)를 따른다.

GitOps 저장소는 Atmo와 같은 다음 파일 구조를 제공해야 한다.

```text
workloads/neople-game-analytics/
├─ api/environments/dev/kustomization.yaml
├─ api/environments/prod/kustomization.yaml
├─ web/environments/dev/kustomization.yaml
└─ web/environments/prod/kustomization.yaml
```

각 `kustomization.yaml`에는 API와 Web 이미지의 `newTag`가 있어야 한다. Worker는 API 이미지와 동일한 이미지를 사용하므로 별도의 Worker 이미지 태그를 두지 않는다. CI는 두 파일의 API/Web `newTag`를 동일한 이미지 태그로 바꾼다.

## 데이터와 Secret 경계

- `DNF_API_KEY`, `CYPHERS_API_KEY`는 이미지에 넣지 않는다.
- 이미지 빌드 과정에서 API Key를 Docker build argument나 파일로 전달하지 않는다.
- API는 GitOps PVC의 공개 검토 JSON 또는 이미지의 데모 JSON만 읽으며, Neople Secret을 주입하지 않는다.
- Worker는 GitOps Secret에서 Key를 받고, 같은 PVC의 `data/public/dashboard.json`을 갱신한다.
- API Key를 사용하는 실데이터 수집은 [게임별 API Key 문서](api-key-separation.md)의 절차를 따른다.
- `dashboard.json`은 공개 전 닉네임·Player ID·원천 응답 포함 여부를 검토한다.

## 현재 브랜치에서의 실행 조건

이 저장소의 원격 기본 주소는 GitHub지만, `.gitlab-ci.yml`은 GitLab으로 미러링된 서비스 저장소에서 실행하는 구성이다. GitLab 프로젝트에 연결되지 않은 상태에서는 파일을 커밋해도 CI가 자동 실행되지 않는다. 현재 CI 파일은 Atmo GitOps의 테스트 브랜치인 `feature/clean-gitops-layout`을 기본 대상으로 둔다.

로컬에는 Docker/Kubernetes 실행 도구가 없어 이미지 빌드와 클러스터 동기화는 GitLab Runner와 실제 GitOps/Argo CD 환경에서 검증한다. Python 테스트는 다음 명령으로 검증한다.

```powershell
python -m pytest -q
```

Docker가 설치된 환경에서는 두 컨테이너를 함께 확인할 수 있다.

```powershell
docker compose up --build
```

브라우저에서 `http://localhost:8080`을 열면 Web 컨테이너가 API 컨테이너의 `/api/dashboard`를 호출한다. 로컬에서 API 컨테이너를 단독 실행할 때도 `http://localhost:8000/healthz`와 `http://localhost:8000/api/dashboard`를 확인할 수 있다.
