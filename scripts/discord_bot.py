import discord
from discord.ext import commands
import os
import requests
import asyncio
from dotenv import load_dotenv
import time

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

def get_workflow_jobs(run_id):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}/jobs"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to get workflow jobs: {response.status_code} - {response.text}")
    return response.json()

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")
    
    try:
        command = await bot.tree.sync()
        print(f"Slash commands synced: {command}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.tree.command(name="analyze", description="Analyze a branch")
async def analyze(interaction: discord.Interaction, branch: str):
    try:
        await interaction.response.send_message(f"Triggering analysis for branch: {branch}")

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
            await interaction.followup.send(f"Workflow triggered successfully for branch: {branch}")
            
            # Wait a bit for the workflow to start
            await asyncio.sleep(5)
            
            # Get the latest workflow run
            runs_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs"
            runs_response = requests.get(runs_url, headers=headers)
            if runs_response.status_code != 200:
                await interaction.followup.send(f"Failed to get workflow runs: {runs_response.status_code}")
                return
                
            runs_data = runs_response.json()
            if not runs_data.get('workflow_runs'):
                await interaction.followup.send("No workflow runs found")
                return
                
            run_id = runs_data['workflow_runs'][0]['id']
            await interaction.followup.send("Waiting for the Snyk scan results... This may take a few minutes.")

            # Poll the GitHub Actions API to check the workflow status
            max_retries = 40  # Increased max retries
            retry_count = 0
            snyk_job_completed = False
            
            while retry_count < max_retries:
                try:
                    workflow_status = get_workflow_status(run_id)
                    status = workflow_status.get('status')
                    
                    # Check specific job status
                    jobs = get_workflow_jobs(run_id)
                    for job in jobs.get('jobs', []):
                        if job['name'] == 'snyk':  # Check specifically for the Snyk job
                            if job['status'] == 'completed':
                                if job['conclusion'] == 'success':
                                    snyk_job_completed = True
                                    break
                                else:
                                    await interaction.followup.send(f"Snyk job failed with conclusion: {job['conclusion']}")
                                    return

                    if snyk_job_completed:
                        # Wait additional time for file system operations to complete
                        await asyncio.sleep(10)
                        await interaction.followup.send("Snyk scan completed. Fetching results...")
                        await send_snyk_results(interaction)
                        break
                    
                    retry_count += 1
                    await asyncio.sleep(15)  # Check every 15 seconds
                    
                except Exception as e:
                    await interaction.followup.send(f"Error checking workflow status: {str(e)}")
                    break
                    
            if retry_count >= max_retries:
                await interaction.followup.send("Timed out waiting for Snyk results")
        else:
            await interaction.followup.send(f"Failed to trigger workflow: {response.status_code} - {response.text}")
            
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {str(e)}")

async def send_snyk_results(interaction):
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Check both possible locations for the file
            possible_paths = [
                "snyk_summary.txt",
                "../../snyk_summary.txt",
                os.path.join(os.getcwd(), "snyk_summary.txt"),
                os.path.join(os.path.dirname(os.getcwd()), "snyk_summary.txt")
            ]
            
            file_found = False
            for file_path in possible_paths:
                if os.path.exists(file_path):
                    with open(file_path, "r") as file:
                        snyk_summary = file.read()
                        file_found = True
                        break
            
            if not file_found:
                if retry_count == max_retries - 1:
                    await interaction.followup.send("No Snyk scan results available after multiple attempts.")
                    await interaction.followup.send(f"Checked paths: {', '.join(possible_paths)}")
                    return
                retry_count += 1
                await asyncio.sleep(5)
                continue

            # Split long messages if needed
            max_length = 2000
            if len(snyk_summary) > max_length:
                chunks = [snyk_summary[i:i + max_length] for i in range(0, len(snyk_summary), max_length)]
                for chunk in chunks:
                    await interaction.followup.send(f"```txt\n{chunk}\n```")
            else:
                await interaction.followup.send(f"```txt\n{snyk_summary}\n```")
            break
                
        except Exception as e:
            if retry_count == max_retries - 1:
                await interaction.followup.send(f"Error sending Snyk results: {str(e)}")
                return
            retry_count += 1
            await asyncio.sleep(5)

if __name__ == "__main__":
    bot.run(TOKEN)
