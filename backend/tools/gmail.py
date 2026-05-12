import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.compose',
          'https://www.googleapis.com/auth/gmail.send']


def get_gmail_service():
    """Get authenticated Gmail API service."""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), '..', 'token.json')
    credentials_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
    
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


async def get_emails() -> str:
    """
    Fetch the last 10 unread emails from inbox.
    
    Returns:
        A formatted string with sender, subject, and snippet for each email
    """
    try:
        service = get_gmail_service()
        
        # Get unread messages
        results = service.users().messages().list(
            userId='me',
            labelIds=['INBOX', 'UNREAD'],
            maxResults=10
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return "No unread emails found."
        
        email_list = []
        for msg in messages:
            # Get full message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            snippet = message.get('snippet', '')
            
            email_list.append(f"From: {sender}\nSubject: {subject}\nSnippet: {snippet}\n")
        
        return "\n---\n".join(email_list)
    
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def draft_email(to: str, subject: str, body: str) -> str:
    """
    Create a draft email.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
    
    Returns:
        Success or error message
    """
    try:
        service = get_gmail_service()
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        # Encode the message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        create_message = {'message': {'raw': encoded_message}}
        
        draft = service.users().drafts().create(
            userId='me',
            body=create_message
        ).execute()
        
        return f"Draft created successfully. Draft ID: {draft['id']}"
    
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


async def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
    
    Returns:
        Success or error message
    """
    try:
        service = get_gmail_service()
        
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        
        # Encode the message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        send_message = {'raw': encoded_message}
        
        sent = service.users().messages().send(
            userId='me',
            body=send_message
        ).execute()
        
        return f"Email sent successfully. Message ID: {sent['id']}"
    
    except HttpError as error:
        return f"An error occurred: {error}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
