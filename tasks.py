# tasks.py (wthpurge 2.0, Direct API Version with Timestamp Logging)

import sys
import os
from datetime import datetime

# --- Add local libraries to Python's path, since Toolforge needs to add libraries manually ---
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# This library must be called after setting path above
import requests

# --- Configuration ---
PAGE_TITLE = 'หน้าหลัก'
API_URL = 'https://th.wikipedia.org/w/api.php'
PAGE_URL = f'https://th.wikipedia.org/wiki/{PAGE_TITLE}'
USER_AGENT = f'TH-MainPage-Purger/2.0 (Toolforge; contact: [[User:Wutkh]])'

# --- Logging Helper ---
def log_message(message):
    """Prints a message with a UTC timestamp."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"[{timestamp}] {message}")

def purge_page():
    """Purges the main page by making direct calls to the MediaWiki API."""
    log_message("Starting the PURGE process with the direct API method...")
    try:
        bot_user = os.environ.get('BOT_USERNAME')
        bot_pass = os.environ.get('BOT_PASSWORD')

        if not bot_user or not bot_pass:
            log_message("FATAL ERROR: Could not find BOT_USERNAME or BOT_PASSWORD in environment variables.")
            return

        # 1. Use a session to handle cookies automatically
        session = requests.Session()
        session.headers.update({'User-Agent': USER_AGENT})

        # 2. Get a login token
        log_message("Step 1: Getting login token...")
        res = session.get(API_URL, params={
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'
        }).json()
        login_token = res['query']['tokens']['logintoken']
        log_message("Login token received.")

        # 3. Log in to the wiki
        log_message("Step 2: Logging in...")
        res = session.post(API_URL, data={
            'action': 'login',
            'lgname': bot_user,
            'lgpassword': bot_pass,
            'lgtoken': login_token,
            'format': 'json'
        }).json()

        if res['login']['result'] != 'Success':
            log_message(f"FATAL ERROR: Login failed. Response: {res}")
            return
        log_message(f"Successfully logged in as {res['login']['lgusername']}.")

        # 4. Get a CSRF token (required for purging)
        log_message("Step 3: Getting CSRF token...")
        res = session.get(API_URL, params={
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        }).json()
        csrf_token = res['query']['tokens']['csrftoken']
        log_message("CSRF token received.")

        # 5. Purge the page
        log_message(f'Step 4: Attempting to purge "{PAGE_TITLE}"...')
        res = session.post(API_URL, data={
            'action': 'purge',
            'titles': PAGE_TITLE,
            'token': csrf_token,
            'format': 'json'
        }).json()

        if 'purge' in res:
            log_message(f'Successfully purged "{PAGE_TITLE}".')
        else:
            log_message(f"Purge action might have failed. Response: {res}")

    except Exception as e:
        log_message(f"An unexpected error occurred during the purge process: {e}")

def archive_page():
    """Sends a request to the Internet Archive to save the main page."""
    log_message("Starting the ARCHIVE process...")
    try:
        archive_url = f'https://web.archive.org/save/{PAGE_URL}'
        headers = {'User-Agent': USER_AGENT}
        log_message(f'Requesting archive for: {PAGE_URL}')
        response = requests.get(archive_url, headers=headers, timeout=300)
        if response.ok:
            log_message(f"Successfully sent archive request. Final URL: {response.url}")
        else:
            log_message(f"Archive request failed with status code: {response.status_code}")
    except Exception as e:
        log_message(f"An error occurred during the archive process: {e}")

def main():
    if len(sys.argv) < 2:
        log_message("Error: No action specified. Use 'purge' or 'archive'.")
        return
    action = sys.argv[1]
    if action == 'purge':
        purge_page()
    elif action == 'archive':
        archive_page()
    else:
        log_message(f"Error: Unknown action '{action}'.")

if __name__ == '__main__':
    main()
