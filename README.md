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
# .env에 API Key와 외부 PostgreSQL 접속 정보 입력

python -m src.collect --game all
python -m src.transform
python -m src.load_postgres --mode replace
```

기본 실행은 외부 관리형 PostgreSQL을 사용합니다. `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SSLMODE`를 DB 서비스가 발급한 값으로 입력한 뒤 실행합니다. `docker compose up -d db`는 로컬 테스트가 필요할 때만 선택적으로 사용합니다.

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

`src.load_postgres`가 외부 관리형 PostgreSQL의 `neople` 스키마에 `data/processed`의 CSV를 적재합니다. 적재가 완료되면 `sql/03_views.sql`의 분석용 View가 생성됩니다. 외부 DB는 일반적으로 SSL 접속을 요구하므로 `.env`의 `POSTGRES_SSLMODE=require`를 사용합니다.

Power BI Desktop에서 `Get data > PostgreSQL database`를 선택해 다음 View를 불러옵니다.

- `neople.vw_dnf_job_growth`
- `neople.vw_dnf_auction_summary`
- `neople.vw_dnf_latest_character`
- `neople.vw_cyphers_character_winrate`
- `neople.vw_cyphers_character_ranking_summary`
- `neople.vw_cyphers_character_positioning`
- `neople.vw_cyphers_item_performance`

이제 갱신 순서는 다음과 같습니다.

```text
API 수집 -> transform -> PostgreSQL 적재 -> Power BI Refresh
```

Power BI `.pbix` 파일은 Power BI Desktop에서 위 View를 최초 연결한 뒤 저장합니다.

## Kubernetes Secret·ConfigMap 설정

클러스터에서 실행할 때 `.env` 파일을 그대로 GitOps 저장소에 넣지 않습니다. 민감한 값은 Kubernetes `Secret`, 일반 실행 설정은 `ConfigMap`으로 분리합니다.

### Secret에 넣을 Key

| Key | 필수 여부 | 설명 |
| --- | --- | --- |
| `NEOPLE_API_KEY` | 필수 | 네오플 Developers에서 발급받은 API Key |
| `POSTGRES_PASSWORD` | 필수 | 외부 관리형 PostgreSQL 접속 비밀번호 |

현재 프로젝트는 위 환경변수 이름을 그대로 읽습니다. 실제 API Key와 비밀번호는 이 채팅이나 GitHub에 입력하지 않습니다.

### Secret 생성 예시

아래 파일은 예시이며 `secret.local.yaml` 같은 로컬 파일로만 사용합니다. GitOps 저장소에는 평문 Secret을 커밋하지 않습니다.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: neople-game-analytics-secret
  namespace: neople
type: Opaque
stringData:
  NEOPLE_API_KEY: "replace_with_your_neople_api_key"
  POSTGRES_PASSWORD: "replace_with_a_strong_postgres_password"
```

```powershell
kubectl create namespace neople
kubectl apply -f secret.local.yaml
```

운영 GitOps에서는 `SealedSecret`, `ExternalSecret` 또는 클라우드 Secret Manager를 사용합니다. 평문 값이 들어간 `secret.local.yaml`은 `.gitignore`에 등록하고 저장소에 커밋하지 않습니다.

### ConfigMap에 넣을 Key

Secret이 아닌 설정은 ConfigMap 또는 Helm values로 관리합니다.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: neople-game-analytics-config
  namespace: neople
data:
  POSTGRES_HOST: "replace_with_managed_postgres_host"
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "replace_with_managed_postgres_database"
  POSTGRES_USER: "replace_with_managed_postgres_user"
  POSTGRES_SSLMODE: "require"
  DNF_SERVERS: "all"
  DNF_FAME_BANDS: "50000:52000,52000:54000,54000:56000"
  DNF_SAMPLE_LIMIT: "30"
  DNF_AUCTION_ITEM_LIMIT: "30"
  CYPHERS_CHARACTER_RANKING_TYPES: "winRate,winCount,killCount,assistCount,exp"
  CYPHERS_RANKING_LIMIT: "1000"
  CYPHERS_TOP_PLAYER_LIMIT: "50"
  CYPHERS_GAME_TYPE: "rating"
  CYPHERS_MATCH_LIMIT: "50"
  CYPHERS_MATCH_DETAIL_LIMIT: "300"
```

`CYPHERS_START_DATE`와 `CYPHERS_END_DATE`를 생략하면 수집 실행일 기준 최근 30일이 사용됩니다. 기간을 고정해 재현하려면 ConfigMap에 다음처럼 추가합니다.

```yaml
  CYPHERS_START_DATE: "2026-08-01 00:00"
  CYPHERS_END_DATE: "2026-08-24 00:00"
```

### Pod 또는 CronJob에서 주입

수집기·변환·적재 컨테이너에는 다음처럼 두 리소스를 모두 주입합니다.

```yaml
envFrom:
  - secretRef:
      name: neople-game-analytics-secret
  - configMapRef:
      name: neople-game-analytics-config
```

이 프로젝트는 외부 관리형 PostgreSQL을 기본으로 사용합니다. Kubernetes에서는 `POSTGRES_HOST`에 관리형 DB의 호스트를 넣고, `POSTGRES_PASSWORD`는 Secret으로 주입합니다. Power BI Desktop도 같은 외부 DB 주소를 사용하며, DB 방화벽에 Power BI 실행 환경의 접속을 허용하거나 VPN·Gateway를 구성해야 합니다. 로컬 PostgreSQL을 사용할 때만 `POSTGRES_HOST=localhost`, `POSTGRES_SSLMODE=disable`을 사용합니다.

### Power BI Embed API Secret

`neople-powerbi-secret`에는 다음 값을 넣습니다.

| Key | 설명 |
| --- | --- |
| `POWERBI_TENANT_ID` | Microsoft Entra 테넌트 ID |
| `POWERBI_CLIENT_ID` | Embed용 Entra 애플리케이션 ID |
| `POWERBI_CLIENT_SECRET` | Embed용 Entra 애플리케이션 Secret |

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: neople-powerbi-secret
  namespace: neople
type: Opaque
stringData:
  POWERBI_TENANT_ID: "replace_with_microsoft_entra_tenant_id"
  POWERBI_CLIENT_ID: "replace_with_microsoft_entra_application_id"
  POWERBI_CLIENT_SECRET: "replace_with_microsoft_entra_client_secret"
```

`POWERBI_WORKSPACE_ID`와 `POWERBI_REPORT_ID`는 `neople-powerbi-config` ConfigMap에 넣습니다. Power BI Service에 Report를 먼저 게시하고, Embed용 Entra 앱을 해당 Workspace의 Member 이상으로 추가해야 `/api/powerbi/embed-config`가 동작합니다.

### 자동화된 Web·API·Worker 구조

```text
GitLab CI
  -> 테스트
  -> Worker/API/Web Docker 이미지 빌드·Push
  -> GitOps 저장소의 Kustomize image tag 변경
  -> Argo CD 또는 Flux 동기화

Kubernetes
  -> analytics-worker CronJob: API 수집 -> transform -> PostgreSQL 적재
  -> analytics-api Deployment: Power BI Embed token 발급
  -> analytics-web Deployment: Power BI 리포트 표시

외부 관리형 PostgreSQL -> Power BI Service -> analytics-web
```

관련 파일:

- `Dockerfile.worker`: 수집·변환·적재 이미지
- `Dockerfile.api`: FastAPI Embed token API 이미지
- `Dockerfile.web`: Power BI 리포트 웹 표시 이미지
- `.gitlab-ci.yml`: 테스트·이미지 Push·선택적 GitOps tag 업데이트
- `deploy/k8s/`: Kustomize 기반 Kubernetes 배포 템플릿

GitLab CI에서 GitOps 자동 업데이트를 사용하려면 다음 CI/CD 변수를 설정합니다.

```text
GITOPS_REPO_HOST_PATH=gitlab.com/your-group/your-gitops-repository.git
GITOPS_ACCESS_TOKEN=마스킹된 GitLab Token
GITOPS_APP_PATH=apps/neople-game-analytics/overlays/prod
```

`GITOPS_ACCESS_TOKEN`은 Repository write 권한이 있는 Masked·Protected 변수로 등록합니다. 실제 Secret 값은 GitOps 저장소에 넣지 않고 SealedSecret 또는 ExternalSecret으로 관리합니다.

## 분석가형 Power BI 구성

Power BI에서는 `powerbi/model.md`의 View 연결 기준을 사용합니다. 분석용 측정값은 `powerbi/measures.dax`에 정리했습니다.

권장 페이지:

1. **분석 개요**: 수집 범위, 표본 정의, 확인 가능한 사실과 한계
2. **던파 성장**: “직업별 성장 격차는 장비 채택 차이와 함께 나타나는가?”
3. **던파 경매장**: “고가 아이템은 가격도 불안정한가?”
4. **사이퍼즈 캐릭터**: “공식 랭킹과 상위 랭커 표본의 성과는 일치하는가?”
5. **사이퍼즈 아이템**: “아이템 조합은 캐릭터 기준 승률보다 높은가?”

각 페이지는 `분석 질문 → 지표 정의 → SQL 검증 → 관찰된 패턴 → 해석·한계` 순서를 유지합니다. 예시 수치는 목업일 뿐이며, 실제 결론은 API 수집 후 갱신된 View를 기준으로 작성합니다.

## 분석상 한계

- 던파 명성 검색은 API가 제공하는 조건과 표본 범위 안에서 해석합니다.
- 던파 경매장 시세는 제공되는 최근 거래 데이터 범위 안에서 분석합니다.
- 사이퍼즈 매칭 데이터는 조회 기간·갱신 주기 제한을 명시합니다.
- 사이퍼즈 공식 캐릭터 랭킹과 상위 랭커 매칭 표본을 모집단으로 구분합니다.
- 사이퍼즈 아이템 성과는 전체 유저가 아니라 자동 수집한 상위 랭커 표본에 대한 결과입니다.
- API 표본으로 전체 이용자 모집단이나 인과관계를 단정하지 않습니다.
