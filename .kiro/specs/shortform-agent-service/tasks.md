# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - content 모드에서 generate_with_llm() 미호출 버그
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: `--mode content` + `OPENAI_API_KEY` 설정 상태에서 `generate_with_llm()`이 호출되지 않는 구체적 케이스로 범위 한정
  - `unittest.mock.patch`로 `generate_with_llm`을 mock 처리 후 `main()`을 `--mode content`로 호출
  - `OPENAI_AVAILABLE = True`, `OPENAI_API_KEY = "sk-test"` 환경에서 mock 호출 횟수가 0임을 확인
  - `hypothesis`로 다양한 유효 JSON 입력에 대해 동일하게 `generate_with_llm()`이 호출되지 않음을 검증
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (이것이 정상 — 버그 존재를 증명)
  - Document counterexamples found: `generate_with_llm()` call_count = 0 (기대값: 1)
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - --mode prompt / --output / --input 기존 동작 보존
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: `--mode prompt` 실행 시 `build_prompt()` 결과가 stdout에 출력됨 (unfixed code)
  - Observe: `--output out.txt` 지정 시 해당 파일에 텍스트가 저장됨 (unfixed code)
  - Observe: `--input custom.json` 지정 시 해당 파일의 JSON이 로딩됨 (unfixed code)
  - Observe: `OPENAI_API_KEY` 없는 content 모드에서 `generate_content_plan()` 결과가 반환됨 (unfixed code)
  - `hypothesis`로 임의의 유효 JSON 입력에 대해 `--mode prompt` 출력이 항상 `build_prompt()` 결과와 동일함을 검증
  - `--output` 경로 지정 시 파일 저장 동작이 항상 발생함을 검증
  - `OPENAI_API_KEY` 없는 content 모드에서 항상 폴백 결과가 반환됨을 검증
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (기존 동작의 베이스라인 확인)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix: content 모드에서 generate_with_llm() 연결

  - [x] 3.1 Implement the fix
    - `shortform-agent-prototype/generate_prompt.py` 상단에 `import sys` 추가
    - `main()`의 `else` 분기를 아래 로직으로 교체:
      - `OPENAI_AVAILABLE and OPENAI_API_KEY` 조건 확인
      - 조건 충족 시: `prompt = build_prompt(data)` → `output = generate_with_llm(prompt)` 실행
      - `OPENAI_AVAILABLE` False 시: `sys.stderr`에 패키지 미설치 경고 출력 후 `generate_content_plan(data)` 폴백
      - `OPENAI_API_KEY` 없을 시: `sys.stderr`에 API 키 미설정 경고 출력 후 `generate_content_plan(data)` 폴백
    - `--mode prompt`, `--output`, `--input` 분기는 일절 수정하지 않음
    - _Bug_Condition: isBugCondition(X) where X.mode = "content"_
    - _Expected_Behavior: OPENAI_AVAILABLE and OPENAI_API_KEY → build_prompt() → generate_with_llm(); else → stderr warning + generate_content_plan()_
    - _Preservation: X.mode != "content" 인 모든 입력에서 main() 동작 불변_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - content 모드에서 generate_with_llm() 호출 확인
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (버그 수정 확인)
    - _Requirements: 2.1, 2.2_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - --mode prompt / --output / --input 기존 동작 보존
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (리그레션 없음 확인)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint - Ensure all tests pass
  - 모든 테스트(탐색 테스트, 보존 테스트)가 통과하는지 확인
  - `pytest shortform-agent-prototype/tests/ -v` 실행 후 결과 검토
  - 실패하는 테스트가 있으면 원인을 분석하고 수정 후 재실행
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. FastAPI 백엔드 서버 구축
  - [x] 5.1 프로젝트 구조 생성 (backend/)
  - [x] 5.2 FastAPI 앱 + 콘텐츠 생성 API 엔드포인트 구현
  - [x] 5.3 Ollama 연동 서비스 레이어 구현
  - [x] 5.4 Pinecone + ChromaDB 벡터 DB 연동

- [x] 6. NestJS BFF 서버 구축
  - [x] 6.1 NestJS 프로젝트 초기화 (bff/)
  - [x] 6.2 FastAPI 프록시 모듈 구현
  - [x] 6.3 API 게이트웨이 라우팅 설정

- [x] 7. React 프론트엔드 UI 구축
  - [x] 7.1 React 프로젝트 초기화 (frontend/)
  - [x] 7.2 콘텐츠 생성 폼 컴포넌트 구현
  - [x] 7.3 결과 표시 컴포넌트 구현
  - [x] 7.4 BFF API 연동

- [x] 8. Docker Compose 통합 & 배포 설정
  - [x] 8.1 각 서비스 Dockerfile 작성
  - [x] 8.2 docker-compose.yml 작성
  - [x] 8.3 README 업데이트
