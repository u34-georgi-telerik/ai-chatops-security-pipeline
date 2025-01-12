import openai
import os

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define the file to analyze
FILE_TO_ANALYZE = "scripts/discord_bot.py"  # Replace with the actual file path

# Read the file content
with open(FILE_TO_ANALYZE, "r") as file:
    code = file.read()

# Send code to OpenAI for analysis
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a code reviewer. Identify bugs, suggest improvements, and highlight best practices."},
        {"role": "user", "content": code},
    ],
)

# Extract and print the response
review = response.choices[0].message.content
print("AI Code Review Results:")
print(review)
