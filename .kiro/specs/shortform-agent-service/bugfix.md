# Bugfix Requirements Document

## 기술 스택

- **Frontend**: React + NestJS (BFF)
- **Backend**: FastAPI
- **Inference Engine**: Ollama
- **Vector DB**: Pinecone, ChromaDB

## Introduction

`generate_prompt.py`의 `main()` 함수에서 `--mode content` 실행 시 OpenAI API를 호출하는 `generate_with_llm()`이 연결되지 않아, 실제 LLM 기반 콘텐츠 생성이 동작하지 않는 버그입니다. 대신 하드코딩된 `generate_content_plan()`만 실행되어 OpenAI API 연동이 실질적으로 무효화됩니다.

전체 서비스는 FastAPI 백엔드 + Ollama 추론 엔진 + Pinecone/ChromaDB 벡터 DB + React/NestJS 프론트엔드로 구성됩니다.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `--mode content`로 실행할 때 THEN the system은 `generate_with_llm()`을 호출하지 않고 하드코딩된 `generate_content_plan()`만 실행한다
1.2 WHEN `OPENAI_API_KEY`가 설정되어 있고 `--mode content`로 실행할 때 THEN the system은 OpenAI API를 호출하지 않고 정적 텍스트를 반환한다
1.3 WHEN `--mode prompt`로 실행할 때 THEN the system은 프롬프트 템플릿을 생성하지만 LLM에 전달하지 않아 실제 콘텐츠 기획이 생성되지 않는다

### Expected Behavior (Correct)

2.1 WHEN `--mode content`로 실행하고 `OPENAI_API_KEY`가 설정되어 있을 때 THEN the system SHALL `build_prompt()`로 프롬프트를 구성한 뒤 `generate_with_llm()`을 호출하여 LLM이 생성한 콘텐츠 기획을 반환한다
2.2 WHEN `--mode content`로 실행하고 `OPENAI_API_KEY`가 설정되어 있지 않을 때 THEN the system SHALL 명확한 오류 메시지를 출력하거나 폴백으로 `generate_content_plan()`을 실행한다
2.3 WHEN `--mode prompt`로 실행할 때 THEN the system SHALL 완성된 프롬프트 텍스트를 출력 또는 파일로 저장한다 (기존 동작 유지)

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `--mode prompt`로 실행할 때 THEN the system SHALL CONTINUE TO 프롬프트 템플릿을 JSON 입력값으로 채워 출력한다
3.2 WHEN `--output` 경로가 지정되었을 때 THEN the system SHALL CONTINUE TO 생성된 텍스트를 해당 파일에 저장한다
3.3 WHEN `--input` 경로가 지정되었을 때 THEN the system SHALL CONTINUE TO 해당 JSON 파일을 입력으로 사용한다
3.4 WHEN `OPENAI_API_KEY`가 없고 `--mode content`로 실행할 때 THEN the system SHALL CONTINUE TO 폴백 콘텐츠 기획(`generate_content_plan()`)을 출력한다

---

## Bug Condition (버그 조건 명세)

**Bug Condition Function:**
```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type CLIArgs
  OUTPUT: boolean

  RETURN X.mode = "content"
END FUNCTION
```

**Property: Fix Checking**
```pascal
FOR ALL X WHERE isBugCondition(X) DO
  result ← main'(X)
  ASSERT (OPENAI_API_KEY가 설정된 경우) result는 LLM이 생성한 텍스트이다
  ASSERT (OPENAI_API_KEY가 없는 경우) result는 오류 메시지 또는 폴백 콘텐츠이다
END FOR
```

**Property: Preservation Checking**
```pascal
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```
