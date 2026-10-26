import json
import os
import sys
from pathlib import Path
from typing import Any

import aisuite as ai
from aisuite.mcp import MCPClient
from dotenv import load_dotenv


# ============================================================
# Configuration
# ============================================================

# Base directory of the current script
BASE_DIR = Path(__file__).resolve().parent

# Path to the .env file
ENV_FILE = BASE_DIR / ".env"

# Load environment variables from the .env file
load_dotenv(ENV_FILE)

# OpenRouter API key read from environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter model name with a default fallback
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-4o-mini",
)


# ============================================================
# System Prompt
# ============================================================

# System prompt that instructs the AI how to calculate
# the domestic gold price step by step
SYSTEM_PROMPT = """
تو یک تحلیلگر بازار طلا هستی. برای پاسخ به سوال کاربر درباره «قیمت طلای داخلی»
دقیقاً این مراحل را طی کن و مراحل را حذف نکن:

۱. با ابزار get_gold_price قیمت جهانی هر انس طلا به دلار را بگیر.
۲. با ابزار get_usd_rate نرخ فعلی دلار به تومان را بگیر.
۳. با استفاده از فرمول زیر قیمت تقریبی هر گرم طلای ۱۸ عیار داخلی را حساب کن:
   قیمت هر گرم طلای ۲۴ عیار (تومان) = (قیمت انس ÷ 31.1) × نرخ دلار
   قیمت هر گرم طلای ۱۸ عیار = قیمت هر گرم طلای ۲۴ عیار × 0.75
۴. نتیجه را به همراه دو عدد خامی که از Tool ها گرفتی (انس جهانی و نرخ دلار)
   به فارسی و به‌صورت شفاف نمایش بده.

نکته: اگر هرکدام از دو Tool خطا داد یا داده برنگرداند، محاسبه را انجام نده
و صریحاً به کاربر بگو کدام داده در دسترس نبود.
"""


# ============================================================
# Helper: Get field from object or dictionary
# ============================================================

def get_field(
    obj: Any,
    field: str,
    default: Any = None,
) -> Any:
    """
    Retrieve a field from either an object or a dictionary.

    If `obj` is a dict, use .get(); otherwise use getattr().
    """

    if isinstance(obj, dict):
        return obj.get(field, default)

    return getattr(obj, field, default)


# ============================================================
# Helper: Format Tool Arguments
# ============================================================

def format_arguments(arguments: Any) -> str:
    """
    Pretty-print tool call arguments as readable JSON.
    """

    # No arguments provided
    if arguments is None:
        return "{}"

    # If arguments are a JSON string, try to parse and re-format
    if isinstance(arguments, str):

        try:
            parsed = json.loads(arguments)

            return json.dumps(
                parsed,
                ensure_ascii=False,
            )

        except json.JSONDecodeError:
            # Not valid JSON; return the raw string
            return arguments

    # Otherwise try to serialize the object directly
    try:
        return json.dumps(
            arguments,
            ensure_ascii=False,
        )

    except TypeError:
        return str(arguments)


# ============================================================
# Helper: Format Tool Result
# ============================================================

def format_tool_result(content: Any) -> str:
    """
    Convert a tool result into a readable string.
    """

    if content is None:
        return "None"

    # If the result is already a string, return it as-is
    if isinstance(content, str):
        return content

    # If the result is a list of MCP content items
    if isinstance(content, list):

        results = []

        for item in content:

            # Try to extract the "text" field from each item
            text_value = get_field(
                item,
                "text",
                None,
            )

            if text_value is not None:
                results.append(str(text_value))
            else:
                results.append(str(item))

        return "\n".join(results)

    # If the result is a dictionary, serialize it as JSON
    if isinstance(content, dict):

        try:
            return json.dumps(
                content,
                ensure_ascii=False,
                indent=2,
            )

        except TypeError:
            return str(content)

    return str(content)


# ============================================================
# Show MCP Tool Calls and Results
# ============================================================

def print_tool_activity(response: Any) -> None:
    """
    Print the tool calls and tool results that aisuite
    produced during the response generation.
    """

    choice = response.choices[0]

    # Intermediate messages contain tool call/result history
    intermediate_messages = getattr(
        choice,
        "intermediate_messages",
        [],
    )

    if not intermediate_messages:
        print("\n🔧 MCP: هیچ Toolای استفاده نشد.")
        return

    found_tool_call = False
    found_tool_result = False

    print("\n" + "=" * 60)
    print("🔧 MCP TOOL ACTIVITY")
    print("=" * 60)

    for message in intermediate_messages:

        role = get_field(
            message,
            "role",
        )

        # ----------------------------------------------------
        # Tool Call
        # ----------------------------------------------------

        tool_calls = get_field(
            message,
            "tool_calls",
            None,
        )

        if tool_calls:

            for tool_call in tool_calls:

                found_tool_call = True

                function = get_field(
                    tool_call,
                    "function",
                    None,
                )

                if function is None:
                    continue

                tool_name = get_field(
                    function,
                    "name",
                    "unknown",
                )

                arguments = get_field(
                    function,
                    "arguments",
                    "{}",
                )

                print("\n📤 TOOL CALL")
                print(f"   Tool      : {tool_name}")
                print(
                    f"   Arguments : "
                    f"{format_arguments(arguments)}"
                )

        # ----------------------------------------------------
        # Tool Result
        # ----------------------------------------------------

        # A tool result message typically has role "tool",
        # a tool_call_id, or a name field
        if (
            role == "tool"
            or get_field(message, "tool_call_id", None)
            or get_field(message, "name", None)
        ):

            content = get_field(
                message,
                "content",
                None,
            )

            tool_name = get_field(
                message,
                "name",
                "unknown",
            )

            found_tool_result = True

            print("\n📥 TOOL RESULT")

            if tool_name:
                print(f"   Tool      : {tool_name}")

            print(
                "   Result:"
            )

            result_text = format_tool_result(
                content
            )

            for line in result_text.splitlines():
                print(f"      {line}")

    if not found_tool_call:
        print("\n📤 هیچ Tool Callای پیدا نشد.")

    if not found_tool_result:
        print("\n📥 نتیجه Tool در intermediate_messages پیدا نشد.")

    print("\n" + "=" * 60)


# ============================================================
# Header
# ============================================================

def print_header() -> None:
    """Print the application header and exit instructions."""

    print()
    print("=" * 60)
    print("                  MCP Finance AI")
    print("=" * 60)
    print("برای خروج، exit یا quit را وارد کنید.")
    print()


# ============================================================
# Print AI Response
# ============================================================

def print_response(
    content: str | None,
) -> None:
    """Print the final AI response in a formatted block."""

    if not content:

        print(
            "\nAI: پاسخی دریافت نشد."
        )

        return

    print("\n" + "-" * 60)
    print("🤖 AI RESPONSE")
    print("-" * 60)
    print(content)
    print("-" * 60)


# ============================================================
# Main
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # Check .env
    # --------------------------------------------------------

    print(f"ENV FILE: {ENV_FILE}")
    print(
        f"ENV EXISTS: "
        f"{ENV_FILE.exists()}"
    )

    print(
        f"OPENROUTER KEY EXISTS: "
        f"{bool(OPENROUTER_API_KEY)}"
    )

    print(
        f"OPENROUTER MODEL: "
        f"{OPENROUTER_MODEL}"
    )

    # Fail fast if the API key is missing
    if not OPENROUTER_API_KEY:

        raise RuntimeError(
            "OPENROUTER_API_KEY در فایل .env تنظیم نشده است."
        )

    # --------------------------------------------------------
    # Create AI client
    # --------------------------------------------------------

    # Configure aisuite to use OpenRouter via the OpenAI-compatible API
    client = ai.Client(
        {
            "openai": {
                "api_key": OPENROUTER_API_KEY,
                "base_url": (
                    "https://openrouter.ai/api/v1"
                ),
            }
        }
    )

    # --------------------------------------------------------
    # Start MCP Server
    # --------------------------------------------------------

    # Launch the MCP server as a subprocess using the current Python interpreter
    mcp = MCPClient(
        command=sys.executable,
        args=[
            str(
                BASE_DIR / "server.py"
            )
        ],
    )

    try:

        # ----------------------------------------------------
        # Load MCP tools
        # ----------------------------------------------------

        # Retrieve callable tools exposed by the MCP server
        tools = mcp.get_callable_tools()

        print("\nMCP tools:")

        for tool in tools:

            print(
                f"  - {tool.__name__}"
            )

        # ----------------------------------------------------
        # Conversation history
        # ----------------------------------------------------

        # Start the conversation with the system prompt
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        # ----------------------------------------------------
        # Interactive prompt
        # ----------------------------------------------------

        print_header()

        while True:

            # ------------------------------------------------
            # Read user input
            # ------------------------------------------------

            try:

                user_input = input(
                    "You: "
                ).strip()

            except KeyboardInterrupt:

                print(
                    "\n\nخروج از برنامه..."
                )

                break

            except EOFError:

                print(
                    "\n\nخروج از برنامه..."
                )

                break

            # ------------------------------------------------
            # Empty input
            # ------------------------------------------------

            if not user_input:
                continue

            # ------------------------------------------------
            # Exit
            # ------------------------------------------------

            if user_input.lower() in {
                "exit",
                "quit",
                "q",
            }:

                print(
                    "\nخروج از برنامه..."
                )

                break

            # ------------------------------------------------
            # Add user message
            # ------------------------------------------------

            messages.append(
                {
                    "role": "user",
                    "content": user_input,
                }
            )

            # ------------------------------------------------
            # Call AI
            # ------------------------------------------------

            try:

                response = (
                    client.chat.completions.create(
                        model=(
                            f"openai:"
                            f"{OPENROUTER_MODEL}"
                        ),
                        messages=messages,
                        tools=tools,
                        # Limit the number of tool-call rounds
                        max_turns=5,
                    )
                )

                # ------------------------------------------------
                # Show MCP activity
                # ------------------------------------------------

                print_tool_activity(
                    response
                )

                # ------------------------------------------------
                # Get final assistant response
                # ------------------------------------------------

                assistant_message = (
                    response.choices[0].message
                )

                # ------------------------------------------------
                # Save full intermediate conversation
                # ------------------------------------------------

                intermediate_messages = getattr(
                    response.choices[0],
                    "intermediate_messages",
                    [],
                )

                if intermediate_messages:

                    # Preserve tool calls/results for future turns
                    messages.extend(
                        intermediate_messages
                    )

                else:

                    # No tool usage; append the assistant reply directly
                    if assistant_message.content:

                        messages.append(
                            {
                                "role": "assistant",
                                "content": (
                                    assistant_message.content
                                ),
                            }
                        )

                # ------------------------------------------------
                # Print final response
                # ------------------------------------------------

                print_response(
                    assistant_message.content
                )

            except Exception as exc:

                print(
                    "\n❌ خطا در پردازش درخواست:"
                )

                print(
                    str(exc)
                )

                # ------------------------------------------------
                # Remove failed user message
                # ------------------------------------------------

                # Roll back the last user message so it can be retried
                if (
                    messages
                    and messages[-1]["role"]
                    == "user"
                    and messages[-1]["content"]
                    == user_input
                ):

                    messages.pop()

    finally:

        # --------------------------------------------------------
        # Close MCP
        # --------------------------------------------------------

        # Always close the MCP connection to release resources
        mcp.close()

        print(
            "\nMCP connection closed."
        )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    main()