import os
from dotenv import load_dotenv
 
load_dotenv()
 
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./customer_support.db")
 
# Groq uses an OpenAI-compatible API, so we just point the openai client
# at Groq's base_url instead of OpenAI's.
LLM_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
 