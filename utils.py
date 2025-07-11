from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_openai_response(prompt, chat_history=None):
    message = chat_history if chat_history else[]
    message.append({"role":"user","content":prompt})

    response = client.chat.completions.create(
        model = "gpt-4",
        messages=message
    )
    reply = response.choices[0].message.content
    message.append({"role":"assistant","content":reply})
    return reply,message
