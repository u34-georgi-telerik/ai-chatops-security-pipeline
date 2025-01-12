import discord
from discord import app_commands
import os
import requests
from dotenv import load_dotenv

# Load environment variables and print debug info immediately
print("Starting bot initialization...")
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "u34-georgi-telerik"
REPO_NAME = "ai-chatops-security-pipeline"

print(f"Discord Token exists: {'Yes' if TOKEN else 'No'}")
print(f"GitHub Token exists: {'Yes' if GITHUB_TOKEN else 'No'}")
print(f"Repository: {REPO_OWNER}/{REPO_NAME}")

# Set up the bot with minimal intents
intents = discord.Intents.default()
intents.messages = True

class Bot(discord.Client):
    def __init__(self):
        print("Initializing Bot class...")
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        print("Setting up command tree...")
        await self.tree.sync()
        print("Command tree synced!")

client = Bot()

@client.event
async def on_ready():
    print(f"Bot is ready! Logged in as {client.user}")

@client.tree.command(name="analyze", description="Analyze a branch")
async def analyze(interaction: discord.Interaction, branch: str):
    print(f"\nReceived analyze command for branch: {branch}")
    
    try:
        await interaction.response.send_message(f"Triggering analysis for branch: {branch}")
        print("Sent initial response to Discord")

        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/ci-cd.yml/dispatches"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",  # Changed from Bearer to token
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "ref": branch
        }

        print(f"Sending request to GitHub:\nURL: {url}")
        response = requests.post(url, headers=headers, json=payload)
        print(f"GitHub API Response: {response.status_code}")
        print(f"Response content: {response.text}")

        if response.status_code == 204:
            await interaction.followup.send("✅ Workflow triggered successfully!")
        else:
            await interaction.followup.send(f"❌ Failed to trigger workflow: {response.status_code}")
            
    except Exception as e:
        print(f"Error in analyze command: {str(e)}")
        await interaction.followup.send(f"❌ Error: {str(e)}")

print("Starting bot...")
client.run(TOKEN)
