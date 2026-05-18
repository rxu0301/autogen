# 📰 뉴스 숏폼 에이전트

주제를 입력하면 RAG를 통해 최신 뉴스 3개를 검색하고, 선택한 뉴스를 요약 스크립트와 썸네일 이미지 생성 프롬프트로 자동 변환하는 풀스택 에이전트 서비스입니다.

---

## 주요 기능

| 단계 | 기능 |
|------|------|
| 1️⃣ 주제 입력 | 검색할 주제를 입력 |
| 2️⃣ 뉴스 선택 | RAG로 검색된 최신 뉴스 3개 중 하나 선택 |
| 3️⃣ 분량 선택 | 20초 / 30초 / 1분 중 선택 |
| 4️⃣ 스크립트 생성 | 정보형 / 감성형 / 자극형 3가지 버전 요약 스크립트 |
| 5️⃣ 썸네일 프롬프트 | 브레이킹 뉴스 / 미니멀 클린 / 임팩트 비주얼 3가지 버전 |
| 📚 라이브러리 | 저장된 결과를 해시태그별로 조회 |

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        사용자 브라우저                            │
│                  React + Vite  (port 3000)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP /api/*
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NestJS BFF  (port 4000)                       │
│          API Gateway · 유효성 검사 · CORS · Swagger              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP /api/v1/*
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend  (port 8000)                    │
│     뉴스 검색 · 스크립트 생성 · 썸네일 프롬프트 · 라이브러리      │
└──────────┬────────────────┬────────────────────────────────────┘
           │                │
           ▼                ▼
┌──────────────────┐  ┌─────────────────────────────────────────┐
│  Ollama          │  │  뉴스 API                               │
│  (port 11434)    │  │  ├─ 네이버 뉴스 API (한국어 권장)        │
│  스크립트/썸네일  │  │  └─ NewsAPI.org (글로벌)                │
│  프롬프트 생성   │  └─────────────────────────────────────────┘
└──────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│  ChromaDB (port 8001) — 라이브러리 저장소                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Frontend | React 18 · Vite 5 · TypeScript |
| BFF | NestJS 10 · Swagger |
| Backend | FastAPI · Python 3.11 · Pydantic v2 |
| LLM 추론 | Ollama (로컬) |
| 뉴스 검색 | 네이버 뉴스 API / NewsAPI.org / Ollama 폴백 |
| 저장소 | ChromaDB (로컬) |
| 컨테이너 | Docker · Docker Compose |

---

## 빠른 시작

### 1. 환경변수 설정

```bash
cp backend/.env.example backend/.env
```

`backend/.env` 파일에서 뉴스 API 키를 설정합니다:

```env
# 네이버 뉴스 API (한국어 뉴스 — 권장)
# https://developers.naver.com/apps/#/register 에서 발급
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret

# NewsAPI.org (선택)
# https://newsapi.org/register 에서 발급
NEWSAPI_KEY=your_api_key
```

> API 키 없이도 동작합니다. Ollama LLM이 뉴스를 시뮬레이션합니다.

### 2. Docker Compose 실행

```bash
docker compose up -d
```

### 3. Ollama 모델 설치

```bash
docker exec -it <ollama_container_id> ollama pull llama3
```

### 4. 접속

- 프론트엔드: http://localhost:3000
- BFF Swagger: http://localhost:4000/api/docs
- Backend Swagger: http://localhost:8000/docs

---

## 로컬 개발

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### BFF (NestJS)

```bash
cd bff
npm install
npm run start:dev
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

---

## API 엔드포인트

### BFF (프론트엔드 → BFF)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/news/search` | 주제 기반 뉴스 검색 |
| `POST` | `/api/news/script` | 뉴스 요약 스크립트 생성 |
| `POST` | `/api/news/thumbnail` | 썸네일 프롬프트 생성 |
| `POST` | `/api/news/save` | 결과 저장 |
| `GET` | `/api/news/library` | 라이브러리 조회 (해시태그 필터) |
| `GET` | `/api/news/health` | 헬스 체크 |

### 라이브러리 조회 예시

```
GET /api/news/library?hashtag=%23AI&limit=20
```

---

## 결과물 구조

각 저장 항목은 다음을 포함합니다:

- **뉴스 요약 스크립트** — 선택한 버전 (정보형 / 감성형 / 자극형)
- **썸네일 이미지 생성 프롬프트** — 3가지 버전 (영문 + 한국어 설명)
- **해시태그** — 뉴스 관련 태그 (라이브러리 필터링에 사용)

---

## 뉴스 검색 우선순위

1. **네이버 뉴스 API** — 한국어 뉴스에 최적화 (NAVER_CLIENT_ID 설정 시)
2. **NewsAPI.org** — 글로벌 뉴스 (NEWSAPI_KEY 설정 시)
3. **Ollama LLM** — API 키 없을 때 뉴스 시뮬레이션 (폴백)
4. **기본 폴백** — Ollama도 미가용 시 기본 뉴스 반환
