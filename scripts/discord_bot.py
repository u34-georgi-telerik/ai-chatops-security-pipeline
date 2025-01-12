# This script listens for /analyze commands and triggers the GitHub Actions workflow using the requests library.

import discord
from discord.ext import commands
import os
import requests

# Load environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "u34-georgi-telerik"  # Replace with your GitHub username
REPO_NAME = "ai-chatops-security-pipeline"  # Replace with your repository name

# Set up the bot
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")

@bot.command()
async def analyze(ctx, branch: str):
    await ctx.send(f"Triggering analysis for branch: {branch}")

    # GitHub Actions API URL
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

bot.run(TOKEN)

async def send_snyk_results(channel):
    if not os.path.exists("snyk_summary.txt"):
        await channel.send("No Snyk scan results available.")
        return

    with open("snyk_summary.txt", "r") as file:
        snyk_summary = file.read()

    await channel.send(f"```\n{snyk_summary}\n```")

@client.event
async def on_message(message):
    if message.content.startswith("/analyze"):
        await message.channel.send("Running Snyk analysis...")
        # Trigger the pipeline (as before)
        # After the pipeline completes:
        await send_snyk_results(message.channel)

