import discord
from discord import app_commands
import os
import requests
import asyncio
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "u34-georgi-telerik"
REPO_NAME = "ai-chatops-security-pipeline"

# Set up the bot with minimal intents
intents = discord.Intents.default()
intents.messages = True

class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = Bot()

@client.event
async def on_ready():
    print(f"Bot is ready! Logged in as {client.user}")
    print(f"GitHub Token available: {'Yes' if GITHUB_TOKEN else 'No'}")
    print(f"Repository: {REPO_OWNER}/{REPO_NAME}")

@client.tree.command(name="analyze", description="Analyze a branch")
async def analyze(interaction: discord.Interaction, branch: str):
    try:
        await interaction.response.send_message(f"Attempting to trigger analysis for branch: {branch}")

        # Debug: Print all environment variables (excluding sensitive values)
        print("Environment check:")
        print(f"REPO_OWNER: {REPO_OWNER}")
        print(f"REPO_NAME: {REPO_NAME}")
        print(f"GitHub Token exists: {'Yes' if GITHUB_TOKEN else 'No'}")

        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/ci-cd.yml/dispatches"
        
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        payload = {
            "ref": branch,
            "inputs": {}  # Add empty inputs even if not needed
        }

        print(f"\nMaking request to GitHub:")
        print(f"URL: {url}")
        print(f"Headers (excluding auth): {{k:v for k,v in headers.items() if k != 'Authorization'}}")
        print(f"Payload: {payload}")

        # Make the request with detailed error handling
        try:
            response = requests.post(url, headers=headers, json=payload)
            print(f"\nResponse status code: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response body: {response.text}")

            if response.status_code == 204:
                await interaction.followup.send("✅ Workflow triggered successfully!")
                
                # Verify the workflow was actually triggered
                verification_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
                verify_response = requests.get(verification_url, headers=headers)
                
                if verify_response.status_code == 200:
                    runs = verify_response.json()
                    if runs.get('workflow_runs'):
                        latest_run = runs['workflow_runs'][0]
                        await interaction.followup.send(
                            f"Latest workflow details:\n"
                            f"Status: {latest_run['status']}\n"
                            f"URL: {latest_run['html_url']}"
                        )
                    else:
                        await interaction.followup.send("⚠️ No workflow runs found after trigger")
                
            elif response.status_code == 404:
                await interaction.followup.send("❌ Error: Workflow file not found. Please check if ci-cd.yml exists in the .github/workflows directory.")
            elif response.status_code == 422:
                await interaction.followup.send("❌ Error: Branch not found or invalid request format.")
            elif response.status_code == 401:
                await interaction.followup.send("❌ Error: Authentication failed. Please check the GitHub token.")
            else:
                await interaction.followup.send(f"❌ Error: Unexpected response code {response.status_code}")

        except requests.exceptions.RequestException as e:
            await interaction.followup.send(f"❌ Network error occurred: {str(e)}")
            
    except Exception as e:
        await interaction.followup.send(f"❌ An error occurred: {str(e)}")
        print(f"Exception details: {str(e)}")

if __name__ == "__main__":
    print("Starting bot...")
    print(f"Current working directory: {os.getcwd()}")
    client.run(TOKEN)
