# 소스

| 폴더 | 내용 | 빌드 결과 |
|---|---|---|
| `lab/` | 실험실 원본 `app.html`, 뇌 반응표 `brain_tables.json`(루밍·빛·냄새), `brain_extra.json`(맛·그루밍·뉴런 차단·3D) | 사이트 루트 `index.html` |
| `swatter/` `pet/` `spider/` `herd/` | 각 게임 원본 `app.html`과 `build.py` | 같은 이름 폴더의 `index.html` |

- 반응표는 `../sim/`의 스크립트로 FlyWire 783 커넥톰 전체를 시뮬레이션해서 만들었다 (`build_tables.py`, `build_odor.py`, `build_extra.py`).
- 각 `build.py`는 작업 환경의 절대·상대 경로(`/home/user/fly-escape/...`)를 가정하고 쓰였다. 다른 곳에서 빌드할 때는 경로를 이 저장소의 `src/lab/brain_*.json`으로 바꾸면 된다.
- `build.py`가 만드는 `local.html`(문자 인코딩 선언 + `vendor/three.min.js`)이 사이트에 올린 파일이다.
