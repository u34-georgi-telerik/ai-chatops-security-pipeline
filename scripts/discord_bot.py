import discord
from discord.ext import commands
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
TOKEN = os.getenv("DISCORD_TOKEN")  # Your Discord bot token
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))  # The Discord channel ID
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # GitHub token for authentication
REPO_OWNER = "u34-georgi-telerik"  # Replace with your GitHub username
REPO_NAME = "ai-chatops-security-pipeline"  # Replace with your repository name

# Set up the bot with the required intents
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")

@bot.command()
async def analyze(ctx, branch: str):
    """
    This command triggers the GitHub Actions workflow for a given branch.
    """
    await ctx.send(f"Triggering analysis for branch: {branch}")

    # GitHub Actions API URL for triggering workflow
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/ci-cd.yml/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    payload = {
        "ref": branch  # Target branch for the workflow
    }

    # Trigger GitHub Actions workflow
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 204:
        await ctx.send(f"Workflow triggered successfully for branch: {branch}")
    else:
        await ctx.send(f"Failed to trigger workflow: {response.status_code} - {response.text}")

    # After triggering the workflow, we want to send Snyk results
    await send_snyk_results(ctx.channel)

async def send_snyk_results(channel):
    """
    This function sends the Snyk results to the Discord channel.
    """
    # Check if Snyk results file exists
    if not os.path.exists("snyk_summary.txt"):
        await channel.send("No Snyk scan results available.")
        return

    # Read and send the results
    with open("snyk_summary.txt", "r") as file:
        snyk_summary = file.read()

    await channel.send(f"**Snyk Analysis Results:**\n```txt\n{snyk_summary}\n```")

# Run the bot
bot.run(TOKEN)
