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
REPO_OWNER = "u34-georgi-telerik"
REPO_NAME = "ai-chatops-security-pipeline"

# Set up the bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Add this line to enable message content intent
bot = commands.Bot(command_prefix="/", intents=intents)

def get_workflow_status(run_id):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to get workflow status: {response.status_code} - {response.text}")
    return response.json()

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")

@bot.command()
async def analyze(ctx, branch: str):
    try:
        await ctx.send(f"Triggering analysis for branch: {branch}")

        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/ci-cd.yml/dispatches"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }
        payload = {
            "ref": branch
        }

        # Trigger GitHub Actions workflow
        response = requests.post(url, headers=headers, json=payload)
        print(f"GitHub API response: {response.status_code} - {response.text}")

        if response.status_code == 204:
            await ctx.send(f"Workflow triggered successfully for branch: {branch}")
            
            # Get the latest workflow run
            runs_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
            runs_response = requests.get(runs_url, headers=headers)
            if runs_response.status_code != 200:
                await ctx.send(f"Failed to get workflow runs: {runs_response.status_code}")
                return
                
            runs_data = runs_response.json()
            if not runs_data.get('workflow_runs'):
                await ctx.send("No workflow runs found")
                return
                
            run_id = runs_data['workflow_runs'][0]['id']
            await ctx.send("Waiting for the Snyk scan results... This may take a few minutes.")

            # Poll the GitHub Actions API to check the workflow status
            max_retries = 20  # Prevent infinite loop
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    workflow_status = get_workflow_status(run_id)
                    status = workflow_status.get('status')
                    conclusion = workflow_status.get('conclusion')

                    if status == 'completed':
                        if conclusion == 'success':
                            await ctx.send("Workflow completed successfully! Fetching Snyk results...")
                            await send_snyk_results(ctx)
                        else:
                            await ctx.send(f"Workflow failed with conclusion: {conclusion}")
                        break
                    
                    retry_count += 1
                    await asyncio.sleep(30)  # Use asyncio.sleep instead of time.sleep
                    
                except Exception as e:
                    await ctx.send(f"Error checking workflow status: {str(e)}")
                    break
                    
            if retry_count >= max_retries:
                await ctx.send("Timed out waiting for workflow completion")
        else:
            await ctx.send(f"Failed to trigger workflow: {response.status_code} - {response.text}")
            
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

async def send_snyk_results(ctx):
    try:
        if not os.path.exists("snyk_summary.txt"):
            await ctx.send("No Snyk scan results available.")
            return

        with open("snyk_summary.txt", "r") as file:
            snyk_summary = file.read()

        # Split long messages if needed
        max_length = 2000  # Discord's message length limit
        if len(snyk_summary) > max_length:
            chunks = [snyk_summary[i:i + max_length] for i in range(0, len(snyk_summary), max_length)]
            for chunk in chunks:
                await ctx.send(f"```txt\n{chunk}\n```")
        else:
            await ctx.send(f"```txt\n{snyk_summary}\n```")
            
    except Exception as e:
        await ctx.send(f"Error sending Snyk results: {str(e)}")

# Add required import
import asyncio

if __name__ == "__main__":
    bot.run(TOKEN)
