# config.py
import os

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") # Personal Access Token with appropriate scopes
GITHUB_REPO_OWNER = "your_github_username_or_org"
GITHUB_REPO_NAME = "your_repo_name"
DISCORD_CHANNEL_ID = 1234567890 # Replace with your Discord channel ID for notifications

# For local development, you might set these directly or use a .env file
# For production, always use environment variables!
