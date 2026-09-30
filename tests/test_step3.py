"""
Run this: python test_step3.py
Tests that the LLM correctly picks a tool, we execute it, and it replies.
"""
import json
from core.llm import call_llm
from knowledge.tools import TOOL_DEFINITIONS, TOOL_REGISTRY

SYSTEM_PROMPT = (
    "You are a customer support agent for AppInSnap, a software company. "
    "Use search_services to answer questions about their services. "
    "IMPORTANT: When answering from search_services results, only state facts that "
    "are explicitly present in the returned context. Do not invent additional services, "
    "certifications, or capabilities that are not mentioned in the context, even if they "
    "sound plausible for a company like this. If the context doesn't fully answer the "
    "user's question, say what you do know and note that you don't have further detail "
    "on the rest. "
    "Use register_complaint when the user wants to file a complaint (make up a user_id like 'test_user' if not given). "
    "Use check_complaint_status when the user gives a complaint number and wants its status."
)


def run(user_message: str):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    reply = call_llm(messages, tools=TOOL_DEFINITIONS)

    if reply.tool_calls:
        messages.append(reply)
        for tool_call in reply.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)
            print(f"  -> LLM called tool: {fn_name}({fn_args})")

            result = TOOL_REGISTRY[fn_name](**fn_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })

        final = call_llm(messages)
        print("  Final reply:", final.content)
    else:
        print("  Final reply (no tool used):", reply.content)


if __name__ == "__main__":
    print("Q1: What fintech services do you offer?")
    run("What fintech services do you offer?")

    print("\nQ2: I want to complain, my project delivery was 2 weeks late")
    run("I want to complain, my project delivery was 2 weeks late. My user id is test_user.")

    print("\nQ3: Check status of SNP-783051")
    run("What's the status of complaint SNP-783051?")