import discord
from discord.ext import commands
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "u34-georgi-telerik"  # Replace with your GitHub username
REPO_NAME = "ai-chatops-security-pipeline"  # Replace with your repository name

# Set up the bot
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="/", intents=intents)

# GitHub API URL for checking workflow status
def get_workflow_status(run_id):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers)
    return response.json()

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

    # Debug logging: Log the GitHub API response
    print(f"GitHub API response: {response.status_code} - {response.text}")

    if response.status_code == 204:
        await ctx.send(f"Workflow triggered successfully for branch: {branch}")

        # Wait for the workflow to complete
        run_id = response.json()['id']  # Get the workflow run ID
        await ctx.send("Waiting for the Snyk scan results... This may take a few minutes.")

        # Poll the GitHub Actions API to check the workflow status
        while True:
            workflow_status = get_workflow_status(run_id)
            status = workflow_status['status']
            conclusion = workflow_status['conclusion']

            if status == 'completed':
                if conclusion == 'success':
                    await ctx.send("Workflow completed successfully! Fetching Snyk results...")
                    await send_snyk_results(ctx)
                else:
                    await ctx.send(f"Workflow failed with status: {conclusion}")
                break
            else:
                # Wait for a while before checking again
                time.sleep(30)  # Check every 30 seconds

    else:
        await ctx.send(f"Failed to trigger workflow: {response.status_code} - {response.text}")

async def send_snyk_results(ctx):
    """
    This function sends the Snyk results to the Discord channel.
    """
    # Check if Snyk results file exists
    if not os.path.exists("snyk_summary.txt"):
        await ctx.send("No Snyk scan results available.")
        return

    # Read and send the results
    with open("snyk_summary.txt", "r") as file:
        snyk_summary = file.read()

    await ctx.send(f"**Snyk Analysis Results:**\n```txt\n{snyk_summary}\n```")

bot.run(TOKEN)
