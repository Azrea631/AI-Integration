# bot.py
import discord
from discord.ext import commands
import requests
import os

from config import DISCORD_BOT_TOKEN
# Assuming your API is running on localhost:5000 for local testing
# For deployment, replace with your API's public URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")

intents = discord.Intents.default()
intents.message_content = True # Required to read message content for commands

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user}')
    print(f'API Base URL: {API_BASE_URL}')

@bot.command(name='githubstats')
async def github_stats(ctx):
    """Fetches and displays GitHub repository statistics."""
    try:
        response = requests.get(f"{API_BASE_URL}/github/repo-stats")
        response.raise_for_status() # Raise an exception for HTTP errors
        stats = response.json()
        
        embed = discord.Embed(
            title=f"GitHub Repository Stats",
            description=f"Stats for `{os.getenv('GITHUB_REPO_OWNER', 'your_github_username_or_org')}/{os.getenv('GITHUB_REPO_NAME', 'your_repo_name')}`",
            color=0x00FF00 # Green
        )
        embed.add_field(name="⭐ Stars", value=stats['stars'], inline=True)
        embed.add_field(name="🍴 Forks", value=stats['forks'], inline=True)
        embed.add_field(name="🐛 Open Issues", value=stats['open_issues'], inline=True)
        embed.add_field(name="🔄 Open PRs", value=stats['open_pull_requests'], inline=True)
        embed.set_footer(text="Data from your custom API")
        await ctx.send(embed=embed)

    except requests.exceptions.RequestException as e:
        await ctx.send(f"Error fetching GitHub stats: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")

@bot.command(name='latestcommit')
async def latest_commit(ctx):
    """Fetches and displays the latest commit to the GitHub repository."""
    try:
        response = requests.get(f"{API_BASE_URL}/github/latest-commit")
        response.raise_for_status()
        commit_info = response.json()

        embed = discord.Embed(
            title="Latest GitHub Commit",
            url=commit_info['url'],
            color=0x00FFFF # Cyan
        )
        embed.add_field(name="Message", value=f"```\n{commit_info['message']}\n```", inline=False)
        embed.add_field(name="Author", value=commit_info['author'], inline=True)
        embed.add_field(name="Date", value=commit_info['date'], inline=True)
        embed.set_footer(text="Data from your custom API")
        await ctx.send(embed=embed)

    except requests.exceptions.RequestException as e:
        await ctx.send(f"Error fetching latest commit: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")

@bot.command(name='createissue')
async def create_issue(ctx, title: str, *, body: str = ""):
    """Creates a new GitHub issue.
    Usage: !createissue "Issue Title" "Optional issue body"
    """
    try:
        payload = {"title": title, "body": body}
        response = requests.post(f"{API_BASE_URL}/github/create-issue", json=payload)
        response.raise_for_status()
        result = response.json()

        if response.status_code == 201:
            await ctx.send(f"✅ Issue created: <{result['issue_url']}> (Issue #{result['issue_number']})")
        else:
            await ctx.send(f"❌ Failed to create issue: {result.get('error', 'Unknown error')}")

    except requests.exceptions.RequestException as e:
        await ctx.send(f"Error communicating with API: {e}")
    except Exception as e:
        await ctx.send(f"An unexpected error occurred: {e}")

# Run the bot
if DISCORD_BOT_TOKEN:
    bot.run(DISCORD_BOT_TOKEN)
else:
    print("DISCORD_BOT_TOKEN not found. Please set it in config.py or as an environment variable.")

