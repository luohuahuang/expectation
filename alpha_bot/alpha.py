import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("ALPHA_API_KEY"),
    base_url=os.environ.get("ALPHA_API_URL"),
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "how to test the SNA project, can you list all of the potential functional test cases.",
        }
    ],

    # Note: An empty string is provided for 'model' to satisfy OpenAI SDK requirements.
    # This parameter is not used for specifying the LLM model in this context.
    # Omitting it would result in an SDK error.
    model="",

    user="huanglh"
)
print(chat_completion.choices[0])