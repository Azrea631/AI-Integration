# api.py
from flask import Flask, request, jsonify
from github import Github
import os
import requests
import hmac
import hashlib

from config import GITHUB_TOKEN, GITHUB_REPO_OWNER, GITHUB_REPO_NAME, DISCORD_CHANNEL_ID

app = Flask(__name__)
github_client = Github(GITHUB_TOKEN)
repo = github_client.get_user(GITHUB_REPO_OWNER).get_repo(GITHUB_REPO_NAME)

# --- GitHub Webhook Secret (Highly Recommended for Security) ---
# Set this as an environment variable or in config.py
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "super_secret_webhook_key")

def verify_signature(payload_body, signature_header):
    """Verify GitHub webhook signature."""
    if not signature_header:
        return False

    sha_name, signature = signature_header.split('=')
    if sha_name != 'sha256': # Or sha1 depending on your GitHub webhook settings
        return False

    mac = hmac.new(GITHUB_WEBHOOK_SECRET.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)

# --- API Endpoint for GitHub Webhooks ---
@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    payload = request.data # Raw payload body

    if not verify_signature(payload, signature):
        app.logger.warning("GitHub webhook signature verification failed!")
        return jsonify({"message": "Signature verification failed"}), 403

    event_type = request.headers.get('X-GitHub-Event')
    data = request.json

    print(f"Received GitHub event: {event_type}")

    if event_type == 'push':
        commit_message = data['head_commit']['message']
        committer_name = data['head_commit']['committer']['name']
        compare_url = data['compare']
        message = f"📢 **New Push on {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}** by {committer_name}:\n`{commit_message}`\n<{compare_url}>"
        send_discord_message(message)
    elif event_type == 'pull_request':
        pr_action = data['action']
        pr_title = data['pull_request']['title']
        pr_number = data['number']
        pr_url = data['pull_request']['html_url']
        pr_user = data['pull_request']['user']['login']
        message = f"🔗 **Pull Request {pr_action} on {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}** by {pr_user}:\n#{pr_number}: `{pr_title}`\n<{pr_url}>"
        send_discord_message(message)
    elif event_type == 'issues':
        issue_action = data['action']
        issue_title = data['issue']['title']
        issue_number = data['issue']['number']
        issue_url = data['issue']['html_url']
        issue_user = data['issue']['user']['login']
        message = f"⚠️ **Issue {issue_action} on {GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}** by {issue_user}:\n#{issue_number}: `{issue_title}`\n<{issue_url}>"
        send_discord_message(message)
    # Add more event types as needed

    return jsonify({"status": "success", "message": f"Event '{event_type}' processed."}), 200

# --- API Endpoints for Discord Bot to Consume ---

@app.route('/github/repo-stats', methods=['GET'])
def get_repo_stats():
    try:
        stars = repo.stargazers_count
        forks = repo.forks_count
        issues_open = repo.get_issues(state='open').totalCount
        pulls_open = repo.get_pulls(state='open').totalCount

        stats = {
            "stars": stars,
            "forks": forks,
            "open_issues": issues_open,
            "open_pull_requests": pulls_open
        }
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/github/latest-commit', methods=['GET'])
def get_latest_commit():
    try:
        latest_commit = repo.get_commits()[0] # Gets the latest commit
        commit_message = latest_commit.commit.message
        commit_author = latest_commit.commit.author.name
        commit_date = latest_commit.commit.author.date.strftime("%Y-%m-%d %H:%M:%S")
        commit_url = latest_commit.html_url

        commit_info = {
            "message": commit_message,
            "author": commit_author,
            "date": commit_date,
            "url": commit_url
        }
        return jsonify(commit_info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/github/create-issue', methods=['POST'])
def create_github_issue():
    data = request.json
    title = data.get('title')
    body = data.get('body', '')
    labels = data.get('labels', [])

    if not title:
        return jsonify({"error": "Issue title is required"}), 400

    try:
        issue = repo.create_issue(title=title, body=body, labels=labels)
        return jsonify({
            "message": "Issue created successfully",
            "issue_url": issue.html_url,
            "issue_number": issue.number
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Helper to send messages to Discord (from API to Bot's channel) ---
def send_discord_message(message_content):
    if not DISCORD_CHANNEL_ID:
        print("DISCORD_CHANNEL_ID not set. Cannot send message to Discord.")
        return

    # To send messages, the API needs to communicate with Discord.
    # The simplest way is to use a Discord webhook URL for the channel,
    # or have the bot actively poll or listen for messages from the API.
    # For simplicity, let's assume you have a Discord webhook URL configured
    # for a specific channel, or you'll forward this via your bot.

    # Option 1: Send directly using a Discord Webhook URL (easiest for API -> Discord)
    # You would need to get this from Discord Channel Settings -> Integrations -> Webhooks
    # DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    # if DISCORD_WEBHOOK_URL:
    #     payload = {"content": message_content}
    #     try:
    #         response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    #         response.raise_for_status()
    #         print(f"Sent message to Discord: {message_content}")
    #     except requests.exceptions.RequestException as e:
    #         print(f"Error sending message to Discord webhook: {e}")
    # else:
    #     print("DISCORD_WEBHOOK_URL not set. Cannot send message directly.")

    # Option 2: More robust - Have the Discord bot listen for API messages (e.g., via a message queue or a separate endpoint)
    # For this example, we'll just print for now and the bot will fetch information.
    # In a real scenario, you'd likely have a messaging system (Redis Pub/Sub, RabbitMQ)
    # or the bot would call back to the API at intervals if direct pushes aren't possible.
    print(f"Would send to Discord channel {DISCORD_CHANNEL_ID}: {message_content}")


if __name__ == '__main__':
    # When deploying, use a production-ready WSGI server like Gunicorn or uWSGI
    # For local testing:
    app.run(host='0.0.0.0', port=5000, debug=True)
