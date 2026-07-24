from collections.abc import Iterator

from openai import OpenAI, APIConnectionError, APIError, RateLimitError
from pydantic import ValidationError

from app.config import get_settings

SYSTEM_PROMPT = """
You are OpsPilot, an AI operations assistant for developers.

Your current responsibilities are:
1. Explain software deployment and operations concepts.
2. Help users understand project status information.
3. Provide concise troubleshooting suggetstions.
4. Clearly state when you do not have access to real server data.

You don't currently have access to any tools or servers.
Never clain that you inspected a real project, process, container, or log.

Above all, always respond in Chinese.
""".strip()

def create_llm_client() -> OpenAI:
  settings = get_settings()

  return OpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    timeout=60.0,
    max_retries=2,
  )

def stream_chat_response(user_message: str) -> Iterator[str]:
    settings = get_settings()
    client = create_llm_client()

    try:
      stream = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
          {
            "role": "system",
            "content": SYSTEM_PROMPT
          },
          {
            "role": "user",
            "content": user_message
          }
        ],
        stream=True,
      )

      for chunk in stream:
        if not chunk.choices:
          continue

        content = chunk.choices[0].delta.content

        if content:
          yield content
    except RateLimitError:
      yield "\n\n[Error] The model service is temporarily rate-limited."

    except APIConnectionError:
      yield "\n\n[Error] Unable to connect to the model service."

    except APIError:
      yield f"\n\n[Error] The model service returned an API error."

    except Exception:
      yield "\n\n[Error] An unexpected error occurred."