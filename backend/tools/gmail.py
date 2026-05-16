# Gmail Tool — ShipStack AI Tool Agent
#
# SETUP (one-time):
# 1. Go to https://console.cloud.google.com and create a project
# 2. Enable the Gmail API under "APIs & Services"
# 3. Create OAuth 2.0 credentials (Desktop app) and download as credentials.json
# 4. Place credentials.json one level above this file (next to your agent's root)
# 5. Run any function once — a browser window will open for you to authorize
# 6. A token.json file will be saved automatically for future runs
#
# REQUIRED PACKAGES:
# pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
]


def _get_gmail_service():
    """Initialize and return an authenticated Gmail API service."""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), '..', 'token.json')
    credentials_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    "credentials.json not found. See setup instructions at the top of this file."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def _extract_body(payload: dict) -> str:
    """Recursively extract plain text body from a Gmail message payload."""
    if payload.get('mimeType') == 'text/plain':
        data = payload.get('body', {}).get('data', '')
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace') if data else ''

    if 'parts' in payload:
        for part in payload['parts']:
            result = _extract_body(part)
            if result:
                return result

    return ''


async def get_emails(max_results: int = 10, unread_only: bool = True) -> str:
    """
    Fetch recent emails from the inbox.

    Args:
        max_results: Number of emails to fetch (defaults to 10)
        unread_only: If True, fetch only unread emails (defaults to True)

    Returns:
        A formatted string with sender, subject, date, and snippet for each email
    """
    try:
        service = _get_gmail_service()

        label_ids = ['INBOX', 'UNREAD'] if unread_only else ['INBOX']
        results = service.users().messages().list(
            userId='me',
            labelIds=label_ids,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            return "No emails found."

        email_list = []
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            snippet = message.get('snippet', '')

            email_list.append(
                f"ID: {msg['id']}\nFrom: {sender}\nDate: {date}\nSubject: {subject}\nPreview: {snippet}"
            )

        return "\n\n---\n\n".join(email_list)

    except HttpError as e:
        return f"Gmail API error: {e.status_code} — {e.reason}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def get_email_body(message_id: str) -> str:
    """
    Fetch the full body of a specific email by its message ID.

    Args:
        message_id: The Gmail message ID (from get_emails or search_emails)

    Returns:
        The full plain text body of the email
    """
    try:
        service = _get_gmail_service()

        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
        body = _extract_body(message['payload'])

        return f"From: {sender}\nDate: {date}\nSubject: {subject}\n\n{body or '[No plain text body found]'}"

    except HttpError as e:
        return f"Gmail API error: {e.status_code} — {e.reason}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def search_emails(query: str, max_results: int = 10) -> str:
    """
    Search emails using Gmail search syntax.

    Args:
        query: Gmail search query (e.g. 'from:ivan@example.com', 'subject:invoice', 'is:unread')
        max_results: Maximum number of results to return (defaults to 10)

    Returns:
        A formatted string listing matching emails with ID, sender, subject, and preview
    """
    try:
        service = _get_gmail_service()

        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])
        if not messages:
            return f"No emails found matching: '{query}'"

        email_list = []
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()

            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            snippet = message.get('snippet', '')

            email_list.append(
                f"ID: {msg['id']}\nFrom: {sender}\nSubject: {subject}\nPreview: {snippet}"
            )

        return f"Results for '{query}':\n\n" + "\n\n---\n\n".join(email_list)

    except HttpError as e:
        return f"Gmail API error: {e.status_code} — {e.reason}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def send_email(to: str, subject: str, body: str, cc: str = "") -> str:
    """
    Send an email immediately.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Plain text email body
        cc: Optional CC email address (defaults to empty)

    Returns:
        Confirmation string with the sent message ID
    """
    try:
        service = _get_gmail_service()

        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        message.attach(MIMEText(body, 'plain'))

        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = service.users().messages().send(
            userId='me',
            body={'raw': encoded}
        ).execute()

        return f"Email sent to {to}. Message ID: {sent['id']}"

    except HttpError as e:
        return f"Gmail API error: {e.status_code} — {e.reason}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def draft_email(to: str, subject: str, body: str, cc: str = "") -> str:
    """
    Save an email as a draft without sending.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Plain text email body
        cc: Optional CC email address (defaults to empty)

    Returns:
        Confirmation string with the draft ID
    """
    try:
        service = _get_gmail_service()

        message = MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        if cc:
            message['cc'] = cc
        message.attach(MIMEText(body, 'plain'))

        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': encoded}}
        ).execute()

        return f"Draft saved. Draft ID: {draft['id']}"

    except HttpError as e:
        return f"Gmail API error: {e.status_code} — {e.reason}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def reply_to_email(message_id: str, body: str) -> str:
    """
    Reply to an existing email thread.

    Args:
        message_id: The Gmail message ID to reply to (from get_emails or search_emails)
        body: Plain text reply body

    Returns:
        Confirmation string with the sent reply message ID
    """
    try:
        service = _get_gmail_service()

        original = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        headers = original['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        thread_id = original['threadId']

        reply_subject = subject if subject.startswith('Re:') else f"Re: {subject}"

        message = MIMEMultipart()
        message['to'] = sender
        message['subject'] = reply_subject
        message['In-Reply-To'] = message_id
        message['References'] = message_id
        message.attach(MIMEText(body, 'plain'))

        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = service.users().messages().send(
            userId='me',
            body={'raw': encoded, 'threadId': thread_id}
        ).execute()

        return f"Reply sent to {sender}. Message ID: {sent['id']}"

    except HttpError as e:
        return f"Gmail API error: {e.status_code} — {e.reason}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def mark_as_read(message_id: str) -> str:
    """
    Mark a specific email as read.

    Args:
        message_id: The Gmail message ID to mark as read

    Returns:
        Confirmation string
    """
    try:
        service = _get_gmail_service()

        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

        return f"Message {message_id} marked as read."

    except HttpError as e:
        return f"Gmail API error: {e.status_code} — {e.reason}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
