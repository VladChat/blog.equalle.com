import os
from openai import OpenAI

def call_llm_local(prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.environ.get("EQUALLE_LLM_MODEL", "gpt-4o")
    client = OpenAI(api_key=api_key)
    system_prompt = (
        "You are a blog post writer for eQualle.com. "
        "Produce only valid Markdown, well structured, SEO friendly, and detailed."
    )

    print("ℹ️ Local mode: {} (Chat API)".format(model))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=7500,
    )
    return resp.choices[0].message.content.strip()
