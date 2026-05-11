<<<<<<< HEAD
# 숏폼 콘텐츠 에이전트 서비스

Ollama 로컬 LLM을 활용해 TikTok·Instagram Reels·YouTube Shorts 등 숏폼 플랫폼에 최적화된 콘텐츠 기획안을 자동 생성하는 풀스택 에이전트 서비스입니다.

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
│          콘텐츠 생성 · 벡터 저장/검색 · 헬스 체크                 │
└──────────┬────────────────┬────────────────────────────────────┘
           │                │
           ▼                ▼
┌──────────────────┐  ┌─────────────────────────────────────────┐
│  Ollama          │  │  Vector DB                              │
│  (port 11434)    │  │  ├─ ChromaDB (로컬, port 8001)          │
│  로컬 LLM 추론   │  │  └─ Pinecone (클라우드, API 키 필요)     │
└──────────────────┘  └─────────────────────────────────────────┘
```

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Frontend | React 18 · Vite 5 · TypeScript |
| BFF | NestJS 10 · Swagger |
| Backend | FastAPI · Python 3.11 · Pydantic v2 |
| LLM 추론 | Ollama (로컬) |
| Vector DB (로컬) | ChromaDB |
| Vector DB (클라우드) | Pinecone |
| 컨테이너 | Docker · Docker Compose |

---

## 사전 요구사항

| 도구 | 최소 버전 | 설치 링크 |
|------|-----------|-----------|
| Docker | 24.x | https://docs.docker.com/get-docker/ |
| Docker Compose | 2.x (Compose V2) | Docker Desktop에 포함 |
| Ollama | 최신 | https://ollama.com/download |

> Pinecone 클라우드 벡터 DB를 사용하려면 [Pinecone](https://www.pinecone.io/) API 키가 필요합니다.  
> API 키 없이도 ChromaDB(로컬)만으로 동작합니다.

---

## 빠른 시작 (Docker Compose)

### 1. 환경 변수 설정

```bash
# Pinecone을 사용하는 경우 (선택)
echo "PINECONE_API_KEY=your-pinecone-api-key" > .env

# Ollama 모델을 변경하려는 경우 (기본값: llama3)
echo "OLLAMA_MODEL=llama3" >> .env
```

### 2. 전체 서비스 실행

```bash
docker compose up -d
```

### 3. Ollama 모델 다운로드 (최초 1회)

```bash
docker exec -it $(docker compose ps -q ollama) ollama pull llama3
```

### 4. 브라우저 접속

| 서비스 | URL |
|--------|-----|
| 프론트엔드 | http://localhost:3000 |
| BFF Swagger | http://localhost:4000/api/docs |
| Backend Swagger | http://localhost:8000/docs |
| ChromaDB | http://localhost:8001 |

### 5. 서비스 중지

```bash
docker compose down
```

---

## 로컬 개발 환경 설정

각 서비스를 독립적으로 실행하는 방법입니다.

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # 필요에 따라 .env 수정
uvicorn app.main:app --reload --port 8000
```

### BFF (NestJS)

```bash
cd bff
npm install
cp .env.example .env
npm run start:dev
```

### Frontend (React)

```bash
cd frontend
npm install
cp .env.example .env        # VITE_BFF_URL=http://localhost:4000/api
npm run dev
```

### Ollama (로컬 LLM)

```bash
# Ollama 서버 실행 (별도 터미널)
ollama serve

# 모델 다운로드
ollama pull llama3
```

---

## 환경 변수 레퍼런스

### Backend (`backend/.env`)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `APP_ENV` | `development` | 실행 환경 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama 서버 주소 |
| `OLLAMA_MODEL` | `llama3` | 사용할 Ollama 모델명 |
| `OLLAMA_TIMEOUT` | `120` | LLM 요청 타임아웃 (초) |
| `PINECONE_API_KEY` | _(없음)_ | Pinecone API 키 (없으면 ChromaDB 전용) |
| `PINECONE_INDEX_NAME` | `shortform-content` | Pinecone 인덱스명 |
| `CHROMA_HOST` | `localhost` | ChromaDB 호스트 |
| `CHROMA_PORT` | `8001` | ChromaDB 포트 |
| `CORS_ORIGINS` | `http://localhost:3000,...` | 허용 CORS 오리진 (쉼표 구분) |

### BFF (`bff/.env`)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `PORT` | `4000` | BFF 서버 포트 |
| `BACKEND_URL` | `http://localhost:8000` | FastAPI 백엔드 주소 |
| `CORS_ORIGIN` | `http://localhost:3000` | 허용 CORS 오리진 |

### Frontend (`frontend/.env`)

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `VITE_BFF_URL` | `http://localhost:4000/api` | BFF API 기본 URL |

---

## API 엔드포인트

### BFF (프론트엔드 → BFF)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/content/generate` | 숏폼 콘텐츠 생성 |
| `POST` | `/api/content/similar` | 유사 콘텐츠 검색 |
| `GET` | `/api/content/health` | 백엔드 헬스 체크 |

### Backend (FastAPI 직접 호출)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/content/generate` | 콘텐츠 생성 |
| `POST` | `/api/v1/content/similar` | 유사 콘텐츠 검색 |
| `GET` | `/api/v1/content/health` | 백엔드 헬스 체크 |
| `GET` | `/health` | 서버 + Ollama 상태 확인 |
| `GET` | `/docs` | Swagger UI |

### 콘텐츠 생성 요청 예시

```json
{
  "interest": "헬스, 다이어트",
  "goal": "팔로워 증가",
  "target_audience": "20대 여성",
  "platform": "TikTok",
  "tone": "자극적 + 유머",
  "duration": "15초",
  "keywords": "뱃살, 홈트",
  "use_llm": true
}
```

---

## Ollama 모델 관리

### 기본 모델 다운로드 및 실행

```bash
# 모델 다운로드
ollama pull llama3

# 사용 가능한 모델 목록 확인
ollama list

# 모델 변경 — .env 파일 수정 후 서비스 재시작
OLLAMA_MODEL=mistral   # 또는 gemma2, qwen2, phi3 등
```

### 로컬 GGUF 모델 사용 (Modelfile 방식)

```bash
# Modelfile이 있는 경우 커스텀 모델 등록
ollama create my-model -f ./Flux2-Klein-9B-True-v2-Q4_K/Modelfile

# .env에서 모델명 변경
OLLAMA_MODEL=my-model
```

### Docker Compose 환경에서 모델 다운로드

```bash
# 컨테이너 실행 중 모델 추가
docker exec -it $(docker compose ps -q ollama) ollama pull llama3

# 또는 컨테이너 이름으로 직접 지정
docker exec -it shortform-ollama-1 ollama pull llama3
```

---

## 트러블슈팅

**Ollama 연결 오류**  
`/health` 엔드포인트에서 `"ollama": {"available": false}`가 반환되면 Ollama 서버가 실행 중인지 확인하세요.

```bash
# 로컬 개발 환경
ollama serve

# Docker 환경
docker compose restart ollama
```

**ChromaDB 연결 오류**  
`CHROMA_HOST`와 `CHROMA_PORT` 설정을 확인하세요. Docker Compose 환경에서는 `CHROMA_HOST=chromadb`, `CHROMA_PORT=8000`(컨테이너 내부 포트)을 사용합니다.

**Pinecone 오류**  
`PINECONE_API_KEY`가 설정되지 않으면 Pinecone 연동이 비활성화되고 ChromaDB만 사용됩니다. 이는 정상 동작입니다.
=======
# autogen
>>>>>>> e0bbc09e45451e328dd359819aee06ce4edd1b9e
