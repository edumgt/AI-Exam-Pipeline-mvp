# Exam AI Pipeline MVP (On-Prem, Docker Compose)

시험 데이터(시계열)를 **입수 → 전처리 → 학습 → 평가**까지 자동으로 수행하고, **관리자 대시보드**에서 상태/이력/지표를 확인할 수 있는 **MVP 레포**입니다.

![](./workflow.png)

## MVP에서 제공하는 것
- **데이터 입수 등록**: 로컬 파일 경로 기반(온프레미스 파일서버/공유폴더 마운트 가정)
- **파이프라인 실행**: `preprocess → train → evaluate` (Celery worker)
- **상태/이력/로그/지표 저장**: PostgreSQL + 파일 로그
- **관리자 UI**: 대시보드(최근 실행), 데이터셋 목록, 실행 목록, 실행 상세(스텝 상태/로그/지표)
- **API 문서**: FastAPI Swagger(`/api/docs`)

> 실제 모델/전처리 로직은 `pipelines/` 폴더의 예시(Scikit-learn)로 구성되어 있으며,
> 여러분의 도메인 전처리/모델로 대체하도록 설계했습니다.

---

## 빠른 시작
### 1) 요구사항
- Docker Desktop(또는 Docker Engine) + Docker Compose

### 2) 실행
```bash
cd exam-ai-pipeline-mvp
cp .env.example .env
docker compose up -d --build
```

### 3) 접속
- Admin UI: http://localhost:8080
- API (Swagger): http://localhost:8080/api/docs

### 4) 샘플 데이터 생성 & 실행
```bash
docker compose exec api python scripts/generate_sample_data.py
docker compose exec api bash scripts/seed_and_run_sample.sh
```

---

## 주요 폴더 구조
```
apps/
  api/        # FastAPI + SQLAlchemy + Celery(작업 트리거)
  web/        # React(Vite) 관리자 페이지
pipelines/    # preprocess/train/evaluate 예시 파이프라인
scripts/      # 샘플 데이터 생성/실행 스크립트
data/         # (볼륨) inbound/processed/models/logs 저장
infra/        # nginx, db init
```

---

## 파이프라인 동작 개요
1. `POST /api/datasets` 로 데이터셋 등록 (예: inbound 폴더 내 파일)
2. `POST /api/runs` 로 실행 생성 (dataset_id + model_type)
3. Celery worker가 스텝을 순서대로 수행
   - preprocess: 정제/변환 후 processed로 저장
   - train: 모델 학습 후 models로 저장
   - evaluate: 성능 지표 산출(metrics.json) + DB 업데이트
4. UI에서 상태/이력/로그/지표 조회

---

## 커스터마이징 포인트
- 전처리: `pipelines/preprocess.py`
- 학습: `pipelines/train.py`
- 평가/지표: `pipelines/evaluate.py`
- 실행 정책/스텝 체인: `apps/api/app/workers/tasks.py`
- 데이터 입수 방식(폴더 감시, SFTP, NAS 등): `apps/api/app/services/ingest.py` (MVP는 경로 기반)

---

## API 요약
- `GET /api/health`
- `POST /api/datasets` / `GET /api/datasets`
- `POST /api/runs` / `GET /api/runs` / `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/logs` (tail)

---

## 라이선스
Internal MVP template. 필요에 따라 사내 정책에 맞춰 조정하세요.

---

## NAS 폴더 감시(Watcher) 동작
이 레포는 `watcher` 서비스가 `/data/inbound` 폴더를 감시하여 파일이 들어오면 자동으로:
1) 파일 완전성 체크(크기 변화가 STABLE_SECONDS 동안 없으면 완료)
2) Dataset 자동 등록 (`POST /api/datasets`)
3) Run 자동 생성 + 파이프라인 실행 (`POST /api/runs`)

### 설정(환경변수)
- `STABLE_SECONDS`: 업로드 완료 판단 기준(초)
- `USE_DONE_FILE=true` 로 설정하면 `*.csv.done` 같은 완료 파일이 존재할 때만 처리합니다.
- `INCLUDE_EXT`: 감시 대상 확장자

### 테스트
```bash
# 샘플 데이터 생성(컨테이너 내부 /data/inbound)
docker compose exec api python scripts/generate_sample_data.py

# watcher 로그 확인
docker compose logs -f watcher
```
---
