from openai import OpenAI

client = OpenAI(
    api_key="your-api_key_here"
)

try:

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how can I use the OpenAI API in Python?"}
        ],
        temperature=0.7,
        max_tokens=200
    )

    text_response = response.choices[0].message.content

    input_token_count = response.usage.prompt_tokens
    output_token_count = response.usage.completion_tokens
    total_token_count = response.usage.total_tokens

    print(f"Response: {text_response}")

    cost = (input_token_count * 0.15 / 1000000) + (output_token_count * 0.60 / 1000000)

    print(f"Cost of this request: ${cost:.10f}")
except Exception as e:
    print(f"An error occurred: {e}")