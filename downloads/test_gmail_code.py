#!/usr/bin/env python3
"""
Test Gmail verification code fetching
"""

import re
import base64
import pickle
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import time

GMAIL_CREDENTIALS_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_credentials.json"
GMAIL_TOKEN_PATH = "/Users/faithtemporosa/tiktok-commenter-dm/tiktok-commenter-dm/downloads/gmail_token.pickle"
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None

    # Load saved credentials
    if os.path.exists(GMAIL_TOKEN_PATH):
        print("Loading saved credentials...")
        with open(GMAIL_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            if not os.path.exists(GMAIL_CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Gmail credentials file not found at {GMAIL_CREDENTIALS_PATH}\n"
                    "Please download your OAuth credentials from Google Cloud Console"
                )
            print("Starting OAuth flow...")
            print("A browser window will open for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_PATH, GMAIL_SCOPES)
            creds = flow.run_local_server(port=8080)
            print("✓ Authentication successful!")

        # Save credentials for next time
        with open(GMAIL_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
            print(f"✓ Credentials saved to {GMAIL_TOKEN_PATH}")

    return build('gmail', 'v1', credentials=creds)


def test_gmail_access():
    """Test Gmail API access"""
    print("=" * 60)
    print("  Testing Gmail API Access")
    print("=" * 60)
    print()

    try:
        service = get_gmail_service()
        print("✓ Successfully connected to Gmail API")
        print()

        # Get recent messages
        print("Fetching recent emails...")
        results = service.users().messages().list(
            userId='me',
            maxResults=5
        ).execute()

        messages = results.get('messages', [])
        print(f"✓ Found {len(messages)} recent messages")
        print()

        # Display recent message subjects
        print("Recent emails:")
        for msg_info in messages[:5]:
            msg = service.users().messages().get(
                userId='me',
                id=msg_info['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject']
            ).execute()

            headers = msg.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            from_addr = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')

            print(f"  - From: {from_addr}")
            print(f"    Subject: {subject}")
            print()

        print("=" * 60)
        print("✓ Gmail API test successful!")
        print("=" * 60)

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_gmail_access()
