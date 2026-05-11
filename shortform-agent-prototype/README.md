# Shortform Content Agent Prototype v1

프로젝트 폴더: `shortform-agent-prototype`

## 목적
사용자의 관심사, 목적, 플랫폼 특성을 반영해 숏폼 콘텐츠 생성 에이전트용 프롬프트를 자동으로 구성하는 프로토타입입니다.

## 구성
- `prompt_template.txt`: LLM에 전달할 에이전트 프롬프트 템플릿
- `generate_prompt.py`: JSON 입력 데이터를 읽어 프롬프트를 생성하고 출력 또는 파일로 저장하는 스크립트
- `sample_input.json`: 테스트용 샘플 입력 데이터
- `sample_output.txt`: 샘플 입력을 기반으로 생성된 최종 프롬프트 예시

## 기능
- 사용자 관심사, 목적, 타겟, 플랫폼, 톤, 길이, 키워드를 하나의 프롬프트로 조합
- 출력 형태를 명시하여 LLM이 콘텐츠 기획을 바로 생성하도록 유도
- CLI 인수로 입력 파일과 출력 파일 지정 가능

## 사용법
1. Python 3.8+ 환경에서 실행
2. `sample_input.json`을 참고해 입력값을 수정
3. 다음 명령어로 샘플 콘텐츠 기획을 생성

```bash
python generate_prompt.py
```

프롬프트 템플릿만 생성하려면

```bash
python generate_prompt.py --mode prompt --output prompt.txt
```

콘텐츠 기획을 파일로 저장하려면

```bash
python generate_prompt.py --output generated_content.txt
```

또는 입력/출력 경로를 지정

```bash
python generate_prompt.py --input sample_input.json --output generated_prompt.txt --mode prompt
```

## 입력 항목
- 사용자 관심사: interest
- 콘텐츠 목적: goal
- 타겟 시청자: target_audience
- 플랫폼: platform
- 콘텐츠 톤: tone
- 길이: duration
- 참고 키워드: keywords

## 출력 항목
- 콘셉트 제안 (3개)
- 최종 선택 콘텐츠 상세 구성
- 최적화 요소 (해시태그, 캡션 등)
- 바이럴 개선 포인트

## 다음 단계
1. OpenAI, local LLM, 또는 API 호출로 프롬프트 결과를 실제 콘텐츠 기획 텍스트로 생성
2. 트렌드 API 연결으로 음악/밈/핫토픽 자동 반영
3. A/B 테스트용 변형 콘텐츠 콘셉트 자동 생성
4. 영상 제작 도구와 연동해 스크립트 → 영상 자동화
