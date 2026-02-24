import argparse
import asyncio
import os
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class Message:
    speaker: str
    content: str


class BotClient:
    name: str

    async def reply(self, topic: str, history: List[Message], round_no: int) -> str:
        raise NotImplementedError


class OpenAIBot(BotClient):
    name = "ChatGPT"

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model

    async def reply(self, topic: str, history: List[Message], round_no: int) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        prompt = build_prompt(topic, history, self.name, round_no)
        res = await client.responses.create(model=self.model, input=prompt)
        return res.output_text.strip()


class GeminiBot(BotClient):
    name = "Gemini"

    def __init__(self, model: str = "gemini-1.5-pro") -> None:
        self.model = model

    async def reply(self, topic: str, history: List[Message], round_no: int) -> str:
        import google.generativeai as genai

        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel(self.model)
        prompt = build_prompt(topic, history, self.name, round_no)

        response = await asyncio.to_thread(model.generate_content, prompt)
        text = getattr(response, "text", "")
        return (text or "").strip()


class ClaudeBot(BotClient):
    name = "Claude"

    def __init__(self, model: str = "claude-3-5-sonnet-20241022") -> None:
        self.model = model

    async def reply(self, topic: str, history: List[Message], round_no: int) -> str:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        prompt = build_prompt(topic, history, self.name, round_no)
        msg = await client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        parts = [block.text for block in msg.content if getattr(block, "type", None) == "text"]
        return "\n".join(parts).strip()


class MockBot(BotClient):
    def __init__(self, name: str) -> None:
        self.name = name

    async def reply(self, topic: str, history: List[Message], round_no: int) -> str:
        return (
            f"[{self.name}] 라운드 {round_no}: '{topic}'에 대해 핵심 쟁점을 요약하고, "
            "이전 의견을 반영해 한 단계 더 구체적인 실행안을 제안합니다."
        )


class ModeratorBot(BotClient):
    name = "Moderator"

    def __init__(self, use_mock: bool, model: str = "gpt-4o-mini") -> None:
        self.use_mock = use_mock
        self.model = model

    async def reply(self, topic: str, history: List[Message], round_no: int) -> str:
        if self.use_mock:
            return (
                "최종 결론: 세 모델의 공통점은 단계적 실험, 평가 지표 정의, 책임 분담입니다. "
                "따라서 1주 PoC → 사용자 피드백 수집 → 개선 반복으로 진행하세요."
            )

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        transcript = "\n".join([f"{m.speaker}: {m.content}" for m in history])
        prompt = (
            "너는 단체 톡방의 사회자다. 아래 대화를 기반으로 합의점과 이견을 정리하고 "
            "실행 가능한 최종 결론을 3~5개 bullet로 제시해라.\n\n"
            f"주제: {topic}\n\n대화:\n{transcript}"
        )
        res = await client.responses.create(model=self.model, input=prompt)
        return res.output_text.strip()


def build_prompt(topic: str, history: List[Message], speaker: str, round_no: int) -> str:
    transcript = "\n".join([f"{m.speaker}: {m.content}" for m in history[-12:]])
    return (
        "너는 AI 단체 톡방 참여자다.\n"
        f"현재 화자: {speaker}\n"
        f"주제: {topic}\n"
        f"현재 라운드: {round_no}\n\n"
        "규칙:\n"
        "1) 4문장 이하로 간결하게 말할 것\n"
        "2) 이전 발언을 1개 이상 인용하거나 반박할 것\n"
        "3) 마지막 문장에 제안/질문을 포함할 것\n\n"
        f"이전 대화:\n{transcript if transcript else '(아직 없음)'}"
    )


async def run_discussion(topic: str, rounds: int, use_mock: bool, output: Optional[str] = None) -> None:
    bots: List[BotClient]
    if use_mock:
        bots = [MockBot("ChatGPT"), MockBot("Gemini"), MockBot("Claude")]
    else:
        bots = [OpenAIBot(), GeminiBot(), ClaudeBot()]

    history: List[Message] = []
    logs: List[str] = []

    print(f"\n🧵 주제: {topic}\n")
    logs.append(f"🧵 주제: {topic}\n")
    for round_no in range(1, rounds + 1):
        print(f"===== Round {round_no} =====")
        logs.append(f"===== Round {round_no} =====")
        for bot in bots:
            try:
                content = await bot.reply(topic, history, round_no)
            except Exception as e:  # noqa: BLE001
                content = f"(응답 실패: {e})"
            message = Message(bot.name, content)
            history.append(message)
            print(f"{bot.name}: {content}\n")
            logs.append(f"{bot.name}: {content}\n")

    moderator = ModeratorBot(use_mock=use_mock)
    conclusion = await moderator.reply(topic, history, rounds + 1)
    print("===== 최종 결론 =====")
    print(conclusion)
    logs.append("===== 최종 결론 =====")
    logs.append(conclusion)

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(logs), encoding="utf-8")
        print(f"\n📄 대화 로그 저장: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ChatGPT/Gemini/Claude 단체 토론 시뮬레이터")
    parser.add_argument("topic", type=str, help="토론 주제")
    parser.add_argument("--rounds", type=int, default=2, help="토론 라운드 수 (기본값: 2)")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="실제 API 호출 없이 모의 응답 사용",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="대화 결과를 파일로 저장할 경로 (예: outputs/chat.txt)",
    )
    return parser.parse_args()


def validate_env(use_mock: bool) -> Optional[str]:
    if use_mock:
        return None
    required = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY"),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        return f"필수 환경변수 누락: {', '.join(missing)}"
    return None


async def main() -> None:
    args = parse_args()
    env_error = validate_env(args.mock)
    if env_error:
        raise SystemExit(env_error)

    await run_discussion(topic=args.topic, rounds=args.rounds, use_mock=args.mock, output=args.output or None)


if __name__ == "__main__":
    asyncio.run(main())
