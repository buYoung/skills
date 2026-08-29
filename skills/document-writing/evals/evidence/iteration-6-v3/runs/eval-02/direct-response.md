# 로컬 API 서버 실행 가이드

이 가이드는 처음 합류한 개발자가 로컬 API 서버를 실행하고, 서버와 데이터베이스 연결 상태를 단계별로 확인할 수 있도록 안내합니다. 완료되면 서버가 `http://localhost:3000`에서 실행되고 `GET /health` 요청에 `{"status":"ok"}`를 반환합니다.

## 사전 조건

다음 도구가 설치되어 있어야 합니다.

- Node.js 22 이상
- Docker
- Git

저장소를 준비한 뒤, 아래 명령은 저장소의 프로젝트 디렉터리에서 실행합니다.

## 실행 절차

### 1. 저장소 준비

저장소를 로컬에 준비하고 프로젝트 디렉터리로 이동합니다.

**확인:** 프로젝트 파일과 `.env.example` 파일이 해당 디렉터리에 있어야 합니다.

### 2. 환경 파일 생성

프로젝트 디렉터리에서 `.env.example`을 `.env`로 복사합니다.

```bash
cp .env.example .env
```

**확인:** `.env` 파일이 생성되어야 합니다.

### 3. PostgreSQL 시작

프로젝트 디렉터리에서 PostgreSQL 컨테이너를 백그라운드로 시작합니다.

```bash
docker compose up -d postgres
```

**확인:** 명령이 오류 없이 완료되고 PostgreSQL 컨테이너가 시작되어야 합니다.

### 4. 의존성 설치

프로젝트 디렉터리에서 잠금 파일에 맞춰 의존성을 설치합니다.

```bash
npm ci
```

**확인:** 명령이 오류 없이 완료되어야 합니다.

### 5. 개발 서버 실행

프로젝트 디렉터리에서 개발 서버를 실행합니다.

```bash
npm run dev
```

**확인:** 로그에 다음 문장이 표시되어야 합니다.

```text
Server running on http://localhost:3000
```

## 최종 확인

서버가 실행 중인 상태에서 `GET /health` 요청을 `http://localhost:3000/health`로 보냅니다.

**정상 응답:**

```json
{"status":"ok"}
```

이 응답이 확인되면 로컬 API 서버 실행과 PostgreSQL 연결 확인이 완료된 것입니다.

## 흔한 문제

### 포트 3000 사용 중

서버가 `http://localhost:3000`에서 시작되지 않거나 포트가 이미 사용 중이라는 오류가 표시되면, 다른 프로세스가 포트 3000을 사용하고 있는지 확인합니다. 해당 프로세스를 정리한 뒤 `npm run dev`를 다시 실행합니다.

### DB connection failed

`DB connection failed`가 표시되면 PostgreSQL이 실행 중인지와 `.env`가 `.env.example`에서 올바르게 생성되었는지 확인합니다. 확인 후 `docker compose up -d postgres`를 다시 실행하고, 개발 서버를 다시 시작합니다.
