# 초파리 뇌 실험실

FlyWire 커넥톰(783판, 뉴런 138,639개, 연결 15,091,983쌍) 전체를 LIF 모델로 시뮬레이션한 반응을 이용해, 블록 세계의 초파리를 움직이는 브라우저 실험실.

## 구성
- `sim/lif.py`: Shiu 외 2024(philshiu/Drosophila_brain_model) 방정식과 파라미터를 numpy 이벤트 구동으로 다시 구현한 시뮬레이터
- `sim/validate.py`, `sim/lateral.py`: 회로 검증 (루밍 → 거대섬유, 좌우 자극 → 하강 뉴런)
- `sim/build_tables.py`, `sim/build_odor.py`: 전체 뇌 반응표 생성 → `brain_tables.json`
- `app.html` + `build.py` → `index.html` (반응표를 넣어 빌드)
- 데이터: `Connectivity_783.parquet`, `Completeness_783.csv` (philshiu/Drosophila_brain_model), 세포 유형 주석 (flyconnectome/flywire_annotations)

## 검증 결과 (전체 뇌, 300ms)
| 자극 | 결과 |
|---|---|
| 자극 없음 | 거대섬유 0Hz |
| LPLC2 20/50/100Hz | 거대섬유 38/77/142Hz |
| LPLC2 한쪽만 | 거대섬유는 양쪽 모두 발화, DNp04는 자극받은 쪽만 발화 |
| Tm3(시각 ON) 한쪽만 | 같은 쪽 DNp07·DNb05·DNbe001 발화 (빛 방향 정보 있음) |
| 광수용세포 R1-6, R7/R8 | 하강 뉴런 반응 0 (억제성 + 모델에 기본 발화 없음) |
| 과일 냄새 수용 뉴런 한쪽만 | 좌우 반응이 거의 같음 (방향 정보 없음) |
| 냄새 세기 | 수용 뉴런당 약 0.4Hz에서 켜지고 1.2Hz에서 포화 (시드 8개 평균) |

## 행동 실험 결과 (헤드리스)
- 탈출: 옆 15/15, 위 15/15, 느린 접근 15/15 탈출. 루밍 뉴런 차단 시 15/15 맞음. 거대섬유가 발화할 때 물체 거리는 빠른 물체 3.1블록, 느린 물체 1.5블록
- 미로(초파리 8마리, 240초, 미로 3개): 뇌 켬 18/24 도착 vs 뇌 끔 10/24
- 주광성(30마리, 60초): 등 근처 비율 뇌 켬 50%, 뇌 끔 3%, 불 끔 3%

## 손으로 만든 부분
감각 변환(루밍 각속도, 눈별 빛 세기, 냄새 적응·로그 변환), 몸 모델(점프·보행·회전 방향), 냄새 확산, 미로의 「세지면 직진, 약해지면 방향 전환」 규칙.

## 사이트
https://fruitfly.blueming.net (GitHub Pages)

## 데이터 출처
- 연결 데이터: [philshiu/Drosophila_brain_model](https://github.com/philshiu/Drosophila_brain_model) (`Connectivity_783.parquet`, `Completeness_783.csv`)
- 세포 유형 주석: [flyconnectome/flywire_annotations](https://github.com/flyconnectome/flywire_annotations)
- FlyWire: Dorkenwald et al. 2024, Schlegel et al. 2024 (Nature). 모델: Shiu et al. 2024 (Nature)
