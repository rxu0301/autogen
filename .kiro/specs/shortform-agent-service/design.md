# shortform-agent-service Bugfix Design

## Overview

`generate_prompt.py`의 `main()` 함수에서 `--mode content` 실행 시 `generate_with_llm()`이 호출되지 않는 버그를 수정합니다.

현재 `main()`은 `--mode content`일 때 항상 `generate_content_plan()`(하드코딩된 폴백)만 실행합니다.
`generate_with_llm()` 함수는 정의되어 있지만 `main()`에서 전혀 연결되지 않아, `OPENAI_API_KEY`가 설정되어 있어도 OpenAI API가 실제로 호출되지 않습니다.

수정 전략:
- `--mode content` 분기에서 `OPENAI_API_KEY` 존재 여부를 확인
- API 키가 있으면 `build_prompt()` → `generate_with_llm()` 경로로 실행
- API 키가 없으면 기존 `generate_content_plan()` 폴백 실행
- `--mode prompt` 동작은 완전히 보존

---

## Glossary

- **Bug_Condition (C)**: 버그가 발생하는 조건 — `--mode content`로 실행될 때
- **Property (P)**: 버그 조건이 충족될 때 기대되는 올바른 동작 — API 키가 있으면 LLM 호출, 없으면 폴백 실행
- **Preservation**: 버그 수정 후에도 변경되지 않아야 하는 기존 동작 — `--mode prompt`, `--output`, `--input` 동작
- **`main()`**: `shortform-agent-prototype/generate_prompt.py`의 진입점 함수. CLI 인수를 파싱하고 모드에 따라 출력을 생성
- **`generate_with_llm(prompt)`**: OpenAI API를 호출해 LLM 기반 콘텐츠를 생성하는 함수. 현재 `main()`에서 호출되지 않음
- **`generate_content_plan(data)`**: 하드코딩된 로직으로 콘텐츠 기획을 생성하는 폴백 함수
- **`build_prompt(data)`**: JSON 입력값을 `prompt_template.txt`에 채워 LLM에 전달할 프롬프트 문자열을 생성하는 함수
- **`OPENAI_API_KEY`**: `.env` 파일 또는 환경변수로 설정되는 OpenAI API 인증 키
- **폴백(Fallback)**: API 키가 없거나 LLM 호출이 불가능할 때 `generate_content_plan()`으로 대체 실행하는 동작

---

## Bug Details

### Bug Condition

`main()` 함수의 `--mode content` 분기에서 `generate_with_llm()`이 연결되지 않아 발생합니다.
`OPENAI_API_KEY` 설정 여부와 무관하게 항상 `generate_content_plan(data)`만 호출됩니다.

**Formal Specification:**
```
FUNCTION isBugCondition(X)
  INPUT: X of type CLIArgs
  OUTPUT: boolean

  RETURN X.mode = "content"
END FUNCTION
```

### Examples

- `python generate_prompt.py --mode content` 실행 + `OPENAI_API_KEY=sk-xxx` 설정됨
  → **실제**: 하드코딩된 `generate_content_plan()` 결과 출력
  → **기대**: `build_prompt()` → `generate_with_llm()` → LLM 생성 콘텐츠 출력

- `python generate_prompt.py --mode content` 실행 + `OPENAI_API_KEY` 미설정
  → **실제**: 하드코딩된 `generate_content_plan()` 결과 출력 (오류 없음)
  → **기대**: 명확한 오류 메시지 출력 또는 폴백 실행 후 폴백임을 알림

- `python generate_prompt.py --mode content --output out.txt` 실행 + API 키 있음
  → **실제**: 하드코딩된 결과가 `out.txt`에 저장됨
  → **기대**: LLM 생성 결과가 `out.txt`에 저장됨

- `python generate_prompt.py --mode content` 실행 + `openai` 패키지 미설치
  → **기대**: ImportError 안내 메시지 출력 또는 폴백 실행 (엣지 케이스)

---

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- `--mode prompt` 실행 시 `build_prompt()`로 프롬프트 템플릿을 채워 출력하는 동작은 변경되지 않아야 한다
- `--output` 경로가 지정된 경우 생성된 텍스트를 해당 파일에 저장하는 동작은 변경되지 않아야 한다
- `--input` 경로가 지정된 경우 해당 JSON 파일을 입력으로 사용하는 동작은 변경되지 않아야 한다
- `OPENAI_API_KEY`가 없을 때 `generate_content_plan()` 폴백이 실행되는 동작은 유지되어야 한다

**Scope:**
`X.mode != "content"`인 모든 입력(즉, `--mode prompt`)은 이번 수정의 영향을 받지 않아야 합니다. 이에 해당하는 동작:
- `--mode prompt` 실행 흐름 전체
- `--output` 파일 저장 로직
- `--input` JSON 로딩 로직
- `load_json()`, `build_prompt()`, `save_text()` 함수 내부 동작

---

## Hypothesized Root Cause

코드 분석 결과, 버그의 원인은 명확합니다:

1. **`main()`의 분기 누락**: `main()` 함수의 `else` 분기(mode == "content")에서 `generate_with_llm()`을 호출하는 코드가 작성되지 않았습니다.
   - 현재 코드: `output = generate_content_plan(data)` (항상 폴백만 실행)
   - 필요한 코드: API 키 존재 여부에 따라 `generate_with_llm()` 또는 `generate_content_plan()` 분기

2. **`generate_with_llm()`과 `build_prompt()`의 연결 부재**: `generate_with_llm(prompt)`는 완전히 구현되어 있고, `build_prompt(data)`도 정상 동작하지만, `main()`에서 두 함수를 연결하는 코드가 없습니다.

3. **API 키 확인 로직 부재**: `main()`에서 `OPENAI_API_KEY` 또는 `OPENAI_AVAILABLE` 플래그를 확인하는 조건 분기가 없어, 폴백 조건을 판단할 수 없습니다.

---

## Correctness Properties

Property 1: Bug Condition - content 모드에서 LLM 호출

_For any_ CLI 실행 인수 X에서 `isBugCondition(X)`가 true(즉, `X.mode = "content"`)이고 `OPENAI_API_KEY`가 설정되어 있을 때, 수정된 `main()`은 `build_prompt(data)`로 프롬프트를 구성한 뒤 `generate_with_llm(prompt)`를 호출하여 OpenAI API가 생성한 콘텐츠 기획 텍스트를 반환해야 한다.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - 비버그 입력의 동작 보존

_For any_ CLI 실행 인수 X에서 `isBugCondition(X)`가 false(즉, `X.mode != "content"`)일 때, 수정된 `main()`은 원본 `main()`과 동일한 결과를 생성하여 `--mode prompt`, `--output`, `--input` 등 기존 동작을 완전히 보존해야 한다.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

---

## Fix Implementation

### Changes Required

**File**: `shortform-agent-prototype/generate_prompt.py`

**Function**: `main()`

**Specific Changes**:

1. **`else` 분기 교체**: 현재 `else: output = generate_content_plan(data)`를 아래 로직으로 교체합니다.

2. **API 키 및 라이브러리 가용성 확인**: `OPENAI_AVAILABLE`과 `OPENAI_API_KEY` 두 조건을 모두 확인합니다.

3. **LLM 호출 경로 추가**: 조건이 충족되면 `build_prompt(data)` → `generate_with_llm(prompt)` 순서로 실행합니다.

4. **폴백 경로 유지**: API 키가 없거나 라이브러리가 없을 때 `generate_content_plan(data)`를 실행하고, 폴백임을 stderr로 알립니다.

5. **예외 처리 추가**: `generate_with_llm()` 호출 시 발생할 수 있는 예외(네트워크 오류, 인증 오류 등)를 잡아 폴백으로 전환하거나 명확한 오류 메시지를 출력합니다.

**수정 전 (현재 코드):**
```python
def main() -> None:
    args = parse_args()
    data = load_json(args.input)

    if args.mode == "prompt":
        output = build_prompt(data)
    else:
        output = generate_content_plan(data)  # ← 항상 폴백만 실행 (버그)

    if args.output:
        save_text(args.output, output)
        print(f"Generated output saved to: {args.output}")
    else:
        print(output)
```

**수정 후 (제안 코드):**
```python
def main() -> None:
    args = parse_args()
    data = load_json(args.input)

    if args.mode == "prompt":
        output = build_prompt(data)
    else:  # mode == "content"
        if OPENAI_AVAILABLE and OPENAI_API_KEY:
            prompt = build_prompt(data)
            output = generate_with_llm(prompt)
        else:
            if not OPENAI_AVAILABLE:
                print("Warning: openai 패키지가 설치되지 않았습니다. 폴백 콘텐츠 기획을 사용합니다.", file=sys.stderr)
            elif not OPENAI_API_KEY:
                print("Warning: OPENAI_API_KEY가 설정되지 않았습니다. 폴백 콘텐츠 기획을 사용합니다.", file=sys.stderr)
            output = generate_content_plan(data)

    if args.output:
        save_text(args.output, output)
        print(f"Generated output saved to: {args.output}")
    else:
        print(output)
```

**추가 import**: `import sys` 추가 필요 (stderr 출력용)

---

## Testing Strategy

### Validation Approach

두 단계로 검증합니다. 먼저 수정 전 코드에서 버그를 재현하는 탐색 테스트를 실행하고, 수정 후 Fix Checking과 Preservation Checking으로 정확성을 검증합니다.

### Exploratory Bug Condition Checking

**Goal**: 수정 전 코드에서 버그를 재현하는 반례(counterexample)를 확인합니다. 루트 원인 분석을 검증하거나 반증합니다.

**Test Plan**: `main()` 함수를 직접 호출하거나 `subprocess`로 CLI를 실행하여 `--mode content` 시 `generate_with_llm()`이 호출되는지 mock으로 확인합니다. 수정 전 코드에서 실패를 관찰합니다.

**Test Cases**:
1. **API 키 있음 + content 모드**: `OPENAI_API_KEY` 설정 후 `--mode content` 실행 → `generate_with_llm()`이 호출되지 않음을 확인 (수정 전 실패)
2. **API 키 없음 + content 모드**: `OPENAI_API_KEY` 미설정 후 `--mode content` 실행 → 오류 메시지 없이 폴백만 실행됨을 확인 (수정 전 실패)
3. **content 모드 출력 타입 확인**: 수정 전 출력이 항상 `generate_content_plan()` 결과임을 확인 (수정 전 실패)
4. **엣지 케이스 - openai 미설치**: `OPENAI_AVAILABLE = False` 상태에서 `--mode content` 실행 → 폴백 실행 여부 확인

**Expected Counterexamples**:
- `generate_with_llm()`이 mock으로 교체되어도 호출 횟수가 0인 것이 관찰됨
- 가능한 원인: `main()`의 `else` 분기에 `generate_with_llm()` 호출 코드 자체가 없음

### Fix Checking

**Goal**: 버그 조건이 충족되는 모든 입력에서 수정된 함수가 올바른 동작을 하는지 검증합니다.

**Pseudocode:**
```
FOR ALL X WHERE isBugCondition(X) DO
  result ← main_fixed(X)
  IF OPENAI_API_KEY가 설정된 경우:
    ASSERT generate_with_llm()이 호출되었다
    ASSERT result는 LLM이 생성한 텍스트이다
  ELSE:
    ASSERT generate_content_plan()이 호출되었다
    ASSERT stderr에 경고 메시지가 출력되었다
END FOR
```

### Preservation Checking

**Goal**: 버그 조건이 충족되지 않는 모든 입력에서 수정된 함수가 원본과 동일한 결과를 생성하는지 검증합니다.

**Pseudocode:**
```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT main_original(X) = main_fixed(X)
END FOR
```

**Testing Approach**: `--mode prompt`는 순수 함수적 동작(동일 입력 → 동일 출력)이므로 property-based testing으로 다양한 JSON 입력에 대해 출력 동일성을 검증하기에 적합합니다.

**Test Cases**:
1. **prompt 모드 출력 보존**: 다양한 JSON 입력에 대해 `--mode prompt` 출력이 수정 전후 동일함을 확인
2. **output 파일 저장 보존**: `--output` 경로 지정 시 파일 저장 동작이 수정 전후 동일함을 확인
3. **input 파일 로딩 보존**: `--input` 경로 지정 시 JSON 로딩 동작이 수정 전후 동일함을 확인
4. **폴백 동작 보존**: API 키 없는 content 모드에서 `generate_content_plan()` 결과가 여전히 반환됨을 확인

### Unit Tests

- `main()`에서 `OPENAI_API_KEY` 있을 때 `generate_with_llm()`이 호출되는지 mock으로 검증
- `main()`에서 `OPENAI_API_KEY` 없을 때 `generate_content_plan()`이 호출되고 stderr 경고가 출력되는지 검증
- `--mode prompt` 실행 시 `build_prompt()`만 호출되고 `generate_with_llm()`은 호출되지 않는지 검증
- `--output` 지정 시 파일 저장 함수가 올바르게 호출되는지 검증

### Property-Based Tests

- 임의의 유효한 JSON 입력에 대해 `--mode prompt` 출력이 수정 전후 동일함을 검증 (Hypothesis 또는 pytest 활용)
- 임의의 JSON 입력에 대해 `build_prompt()` 출력이 항상 모든 입력 필드를 포함하는지 검증
- API 키 없는 content 모드에서 임의 입력에 대해 항상 폴백 결과가 반환됨을 검증

### Integration Tests

- 실제 CLI 명령어(`subprocess`)로 `--mode prompt` 실행 후 출력 형식 검증
- `--mode content` + API 키 없음 실행 후 폴백 출력 및 stderr 경고 메시지 검증
- `--mode content` + `--output` 지정 실행 후 파일 생성 및 내용 검증
- (선택) 실제 OpenAI API 키로 `--mode content` 실행 후 LLM 응답 형식 검증
