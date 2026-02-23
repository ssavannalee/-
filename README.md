# 멀티 챗봇 단체 톡방 토론 프로그램

`ChatGPT`, `Gemini`, `Claude`가 한 방에서 같은 주제로 번갈아 발언하고, 마지막에 사회자(Moderator)가 결론을 정리하는 CLI 프로그램입니다.

## 기능
- 3개 모델이 라운드 기반으로 순차 발언
- 이전 대화 맥락(history)을 참고해 응답 생성
- 마지막에 요약/실행안 중심의 최종 결론 출력
- `--mock` 모드로 API 키 없이 동작 확인 가능

## 설치
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 환경변수 설정
`.env.example`를 참고해 아래 키를 설정하세요.

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`

예시:
```bash
export OPENAI_API_KEY="..."
export GEMINI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
```

## 실행
### 1) 모의 모드(권장: 먼저 동작 검증)
```bash
python multi_chatroom.py "우리 팀의 AI 도입 전략" --rounds 2 --mock
```

### 2) 실제 API 모드
```bash
python multi_chatroom.py "우리 팀의 AI 도입 전략" --rounds 2
```

## 구조
- `OpenAIBot`, `GeminiBot`, `ClaudeBot`: 각 모델 API 클라이언트
- `MockBot`: 키 없이 로컬에서 흐름 테스트
- `ModeratorBot`: 전체 대화를 종합해 결론 생성
- `build_prompt`: 각 턴 프롬프트 템플릿

## 확장 아이디어
- 발언 길이 제한/스타일 커스터마이즈
- 찬반 역할 분담(예: Claude=비판적 검토자)
- 웹 UI(예: Streamlit)로 실시간 채팅처럼 시각화
- 발언 로그 저장(JSON/SQLite)
