import asyncio
import os
import uuid

from google import genai

from runner.state_store import create_agent, update_agent

SHORT_TASK_THRESHOLD_S = int(os.environ.get("SHORT_TASK_THRESHOLD_S", "5"))


async def spawn_agent(action: str, payload: str, model: str, timeout: int) -> tuple[str, str | None]:
    """
    Spawn an LLM agent.

    Short tasks (timeout <= SHORT_TASK_THRESHOLD_S): awaited inline, result returned.
    Long tasks: scheduled as asyncio.Task, None returned — caller polls state.
    """
    agent_id = str(uuid.uuid4())
    await create_agent(agent_id)

    if timeout <= SHORT_TASK_THRESHOLD_S:
        result = await _run_agent(agent_id, action, payload, model)
        return agent_id, result

    asyncio.create_task(_run_agent(agent_id, action, payload, model))
    return agent_id, None


async def _run_agent(agent_id: str, action: str, payload: str, model: str) -> str:
    await update_agent(agent_id, "RUNNING")
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = await client.aio.models.generate_content(
            model=model,
            contents=f"Action: {action}\n\n{payload}",
        )
        result: str = response.text
        await update_agent(agent_id, "DONE", result)
        return result
    except Exception as e:
        await update_agent(agent_id, "ERROR", str(e))
        raise
