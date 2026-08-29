# 현재 방식의 CI/CD와 GitOps

## 목적

현재 분석 방식은 Power BI Embedded나 PostgreSQL API가 아니라 **정제된 대시보드 JSON을 제공하는 읽기 전용 API와 정적 Web 화면**이다.

따라서 컨테이너를 다음 두 개로 나눈다.

| 이미지 | 역할 |
| --- | --- |
| `api` | 검토된 `dashboard.json`을 `/api/dashboard`로 제공하고 `/healthz` 응답 |
| `web` | Nginx로 HTML·CSS·JavaScript를 제공하고 `/api/dashboard`를 API에 프록시 |

API 컨테이너는 Neople API를 직접 호출하지 않으며 API Key를 포함하지 않는다. 데이터 수집·정제는 로컬 또는 별도 승인된 데이터 준비 단계에서 실행한다. 데이터가 없을 때 이미지에는 저장소의 데모 JSON이 포함된다.

## Atmo와 동일한 배포 흐름

```text
GitLab CI
  → Python 테스트·compile 검사
  → API Docker 이미지 빌드·Push
  → Web Docker 이미지 빌드·Push
  → GitOps 저장소 API/Web Kustomize newTag 변경
  → Argo CD 또는 Flux 동기화
  → Kubernetes API + Web 배포
```

이미지는 두 개 모두 동일한 커밋 기준 태그를 사용한다.

- `dev` 브랜치: `dev-$CI_COMMIT_SHORT_SHA`
- SemVer Git tag: `vMAJOR.MINOR.PATCH`

GitOps 커밋에는 `[skip ci]`를 넣어 GitOps 저장소의 검증 파이프라인이 불필요하게 반복되지 않게 한다.

## 저장소 파일

- [`.gitlab-ci.yml`](../../.gitlab-ci.yml): 테스트, API/Web 이미지 빌드·Push, GitOps 태그 변경
- [`Dockerfile.api`](../../Dockerfile.api): FastAPI 읽기 전용 API 이미지
- [`Dockerfile.web`](../../Dockerfile.web): Nginx 정적 Web 이미지
- [`docker-compose.yml`](../../docker-compose.yml): API/Web 로컬 통합 실행 예시
- [`apps/api/main.py`](../../apps/api/main.py): 대시보드 JSON API
- [`deploy/nginx/web.conf`](../../deploy/nginx/web.conf): Web → API 프록시
- [`ci/update-gitops-tags.sh`](../../ci/update-gitops-tags.sh): API/Web `newTag` 동시 변경

## GitLab CI/CD 변수

GitLab Container Registry 관련 `CI_REGISTRY`, `CI_REGISTRY_IMAGE`, `CI_REGISTRY_USER`, `CI_REGISTRY_PASSWORD`는 GitLab 기본 제공 변수를 사용한다.

GitOps 태그 변경 Job을 활성화하려면 다음 변수를 GitLab CI/CD Variables에 등록한다.

| 변수 | 용도 |
| --- | --- |
| `GITOPS_REPO_HOST_PATH` | GitOps 저장소의 호스트 경로. 예: `gitlab.com/group/gitops.git` |
| `GITOPS_PUSH_TOKEN` | GitOps 저장소 Push 권한이 있는 토큰. Masked·Protected 권장 |
| `GITOPS_PUSH_TOKEN_USER` | 토큰에 대응하는 사용자명 |
| `GITOPS_BRANCH` | GitOps 대상 브랜치. 예: `feature/clean-gitops-layout` 또는 `main` |
| `GITOPS_APP_PATH` | API/Web 환경 디렉터리의 기준 경로. 기본값: `workloads/neople-game-analytics` |

GitOps 저장소는 Atmo와 같은 다음 파일 구조를 제공해야 한다.

```text
workloads/neople-game-analytics/
├─ api/environments/dev/kustomization.yaml
├─ api/environments/prod/kustomization.yaml
├─ web/environments/dev/kustomization.yaml
└─ web/environments/prod/kustomization.yaml
```

각 `kustomization.yaml`에는 해당 이미지의 `newTag`가 있어야 한다. CI는 두 파일의 `newTag`를 동일한 이미지 태그로 바꾼다.

## 데이터와 Secret 경계

- `DNF_API_KEY`, `CYPHERS_API_KEY`는 API/Web 이미지에 넣지 않는다.
- 이미지 빌드 과정에서 API Key를 Docker build argument나 파일로 전달하지 않는다.
- API/Web은 이미지에 포함된 공개 검토 JSON 또는 마운트된 JSON만 읽는다.
- API Key를 사용하는 실데이터 수집은 [게임별 API Key 문서](api-key-separation.md)의 절차를 따른다.
- `dashboard.json`은 공개 전 닉네임·Player ID·원천 응답 포함 여부를 검토한다.

## 현재 브랜치에서의 실행 조건

이 저장소의 원격 기본 주소는 GitHub지만, `.gitlab-ci.yml`은 GitLab으로 미러링된 서비스 저장소에서 실행하는 구성이다. GitLab 프로젝트에 연결되지 않은 상태에서는 파일을 커밋해도 CI가 자동 실행되지 않는다.

로컬에는 Docker/Kubernetes 실행 도구가 없어 이미지 빌드와 클러스터 동기화는 GitLab Runner와 실제 GitOps/Argo CD 환경에서 검증한다. Python 테스트는 다음 명령으로 검증한다.

```powershell
python -m pytest -q
```

Docker가 설치된 환경에서는 두 컨테이너를 함께 확인할 수 있다.

```powershell
docker compose up --build
```

브라우저에서 `http://localhost:8080`을 열면 Web 컨테이너가 API 컨테이너의 `/api/dashboard`를 호출한다. 로컬에서 API 컨테이너를 단독 실행할 때도 `http://localhost:8000/healthz`와 `http://localhost:8000/api/dashboard`를 확인할 수 있다.
