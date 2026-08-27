# 게임별 Neople API Key 분리

## 변경 배경

기존 수집기는 던전앤파이터와 사이퍼즈에 하나의 `NEOPLE_API_KEY` 환경변수를 공통으로 사용했다.

그러나 Neople Open API는 게임별로 발급된 API Key를 사용해야 한다. 다른 게임용으로 발급된 Key를 호출에 사용하면 `API005`(해당 게임으로 발급되지 않은 API Key)가 반환될 수 있으므로, 현재 수집 파이프라인에서는 게임별 Key를 분리한다.

공식 참고 문서:

- [Neople API 공통 가이드](https://developers.neople.co.kr/contents/guide/pages/all)
- [Neople API 응답 코드](https://developers.neople.co.kr/contents/guide/pages/code)
- [던전앤파이터 API 문서](https://developers.neople.co.kr/contents/apiDocs)
- [사이퍼즈 API 문서](https://developers.neople.co.kr/contents/apiDocs/cyphers)

## 현재 환경변수

`.env`에는 다음 두 Key를 각각 입력한다.

```env
DNF_API_KEY=발급받은_던파_API_KEY
CYPHERS_API_KEY=발급받은_사이퍼즈_API_KEY
```

실제 Key는 로컬 `.env`에만 저장하고, GitHub·README·HTML·JavaScript·공개 JSON에는 입력하지 않는다. 저장소에 제공되는 [`.env.example`](../../.env.example)에는 실제 값 대신 예시 문자열만 기록한다.

## 기존 `.env`에서 변경하는 방법

기존에 아래처럼 작성했다면:

```env
NEOPLE_API_KEY=기존에_입력한_Key
```

다음처럼 변경한다.

```env
DNF_API_KEY=던파용으로_발급받은_Key
CYPHERS_API_KEY=사이퍼즈용으로_발급받은_Key
```

기존 Key가 어느 게임용인지 불명확하면 Neople Developers의 애플리케이션 목록에서 확인하거나 게임별로 새 Key를 발급받는다. 기존 `NEOPLE_API_KEY` 변수는 현재 수집기에서 읽지 않는다.

## 실행별 필요한 Key

수집기는 선택한 게임에 필요한 클라이언트만 만든다. 따라서 한 게임만 수집할 때 다른 게임의 Key까지 입력할 필요가 없다.

| 명령 | 필요한 설정 |
| --- | --- |
| `python -m src.collect --game dnf` | `DNF_API_KEY` |
| `python -m src.collect --game cyphers` | `CYPHERS_API_KEY` |
| `python -m src.collect --game all` | `DNF_API_KEY`, `CYPHERS_API_KEY` |
| `python -m src.collect --game dnf --dry-run` | 실제 Key 불필요 |
| `python -m src.collect --game cyphers --dry-run` | 실제 Key 불필요 |

예를 들어 던파 데이터만 먼저 수집하려면 다음처럼 실행한다.

```powershell
python -m src.collect --game dnf --dry-run
python -m src.collect --game dnf
```

사이퍼즈 데이터는 사이퍼즈용 Key와 닉네임 또는 Player ID를 설정한 후 별도로 수집한다.

```powershell
python -m src.collect --game cyphers --dry-run
python -m src.collect --game cyphers
```

## 구현 변경

- `src/collect.py`가 던파용 `NeopleClient`와 사이퍼즈용 `NeopleClient`를 분리해 생성한다.
- `--game dnf` 실행 시 `DNF_API_KEY`만 읽는다.
- `--game cyphers` 실행 시 `CYPHERS_API_KEY`만 읽는다.
- `--game all` 실행 시 두 환경변수를 모두 읽는다.
- `src/neople_api.py`는 Key가 비어 있을 때 실제 변수명을 포함한 오류를 표시한다.

## 공개 배포와 보안

API Key는 정적 웹 대시보드에 필요하지 않다. 로컬에서 API를 호출해 원천 데이터를 만들고, 정제·비식별 검토가 끝난 공개용 집계 JSON만 웹사이트에 배포한다.

공개 전 다음 항목을 확인한다.

- `data/raw` 원천 응답을 공개하지 않는다.
- 닉네임, Player ID 등 공개가 불필요한 식별자를 집계 JSON에서 제거하거나 검토한다.
- API Key가 로그, 커밋, 웹 산출물에 포함되지 않았는지 확인한다.
- 자동 수집을 도입할 경우 두 Key를 각각 GitHub Actions Secret으로 주입한다.

상세한 전체 환경변수 목록과 Power BI·PostgreSQL 등 현재 사용하지 않는 이전 설정은 [`secret-config.md`](secret-config.md)를 참고한다.
