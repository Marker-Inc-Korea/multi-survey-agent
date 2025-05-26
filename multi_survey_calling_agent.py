# multi_survey_calling_agent.py

import logging
from pathlib import Path
import json
import asyncio
from livekit.agents import (
    Agent,
    get_job_context,
    AgentSession,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    RoomInputOptions,
    ChatContext,
    function_tool,
)

from openai.types.beta.realtime.session import TurnDetection

from livekit.plugins import openai, noise_cancellation
from livekit.api import DeleteRoomRequest

from dotenv import load_dotenv

from utils import load_prompt, load_questions
from schema import SurveyState

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

logger = logging.getLogger("multi-agent-survey")
logger.setLevel(logging.INFO)

csv_file_path = Path(__file__).parent / "survey_data.csv"


RunContext_T = RunContext[SurveyState]


class BaseAgent(Agent):
    async def on_enter(self) -> None:
        agent_name = self.__class__.__name__
        userdata = self.session.userdata
        chat_ctx = self.chat_ctx.copy()

        chat_ctx.add_message(
            role="system",
            content=f"You are the {agent_name}. For SurveyAgent: If the user answers a question, you MUST record the answer by calling `record_answer` function. That's the first thing you should do. {userdata.summarize()}. For GoodbyeAgent: save the survey.",
        )
        await self.update_chat_ctx(chat_ctx)
        self.session.generate_reply()


class SurveyAgent(BaseAgent):
    def __init__(self, chat_ctx: ChatContext = None):
        super().__init__(
            instructions=load_prompt("survey_prompt.yaml"),
            chat_ctx=chat_ctx,
        )

    @function_tool()
    async def record_answer(self, context: RunContext_T, answer: str):
        """Use this tool to record the answer for the current question. Call this tool only after receiving an actual answer from the user."""
        context.userdata.record_answer(answer)

        new_summary = context.userdata.summarize()

        updated_ctx = self.chat_ctx.copy()
        updated_ctx.items = [msg for msg in updated_ctx.items if msg.role != "system"]
        updated_ctx.add_message(role="system", content=f"[Updated]\n{new_summary}")
        await self.update_chat_ctx(updated_ctx)

        if context.userdata.get_current_question():
            await self.session.generate_reply()
            return self
        else:
            return GoodbyeAgent(chat_ctx=self.chat_ctx)


class GoodbyeAgent(BaseAgent):
    def __init__(self, chat_ctx: ChatContext = None):
        super().__init__(
            instructions="Thank for their answers and end the call by saving the survey when it's complete.",
            chat_ctx=chat_ctx,
        )

    @function_tool
    async def save_survey_answers(self):
        """Use this when survey is completed to save the records"""
        import pandas as pd

        state: SurveyState = self.session.userdata
        df = pd.read_csv(csv_file_path, dtype=str)
        job_ctx = get_job_context()
        metadata = json.loads(job_ctx.job.metadata)
        idx = metadata.get("row_index", 1) - 1
        df.at[idx, "Answer"] = json.dumps(
            {q.id: q.answer for q in state.questions if q.status == "answered"},
            ensure_ascii=False,
        )
        df.at[idx, "Status"] = "Completed"
        df.to_csv(csv_file_path, index=False)

        await asyncio.sleep(5)
        await job_ctx.api.room.delete_room(DeleteRoomRequest(room=job_ctx.room.name))

        return None, f"[Call ended]"


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    metadata = json.loads(ctx.job.metadata)
    row_index = metadata.get("row_index", 1)

    session = AgentSession[SurveyState](
        userdata=SurveyState(questions=load_questions("survey_questions.yaml")),
        llm=openai.realtime.RealtimeModel(
            model="gpt-4o-mini-realtime-preview",
            turn_detection=TurnDetection(
                type="server_vad",
                threshold=0.8,
                prefix_padding_ms=300,
                silence_duration_ms=500,
                create_response=True,
                interrupt_response=True,
            ),
        ),
    )

    await session.start(
        agent=SurveyAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(entrypoint_fnc=entrypoint, agent_name="multi-survey-agent")
    )
