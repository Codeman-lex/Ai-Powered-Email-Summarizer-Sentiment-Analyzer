import os
import json
from flask import Flask, redirect, request, url_for, session, render_template, flash
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from openai import OpenAI
from dotenv import load_dotenv
from flask_session import Session
from email.mime.text import MIMEText

# Load environment variables
load_dotenv()

# Configure Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)

# OpenAI configuration
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Google OAuth configuration
CLIENT_CONFIG = {
    'web': {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'redirect_uris': [os.getenv('GOOGLE_REDIRECT_URI')],
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
    }
}

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def credentials_to_dict(credentials):
    """Convert Credentials object to dictionary."""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }


def dict_to_credentials(credentials_dict):
    """Convert dictionary to Credentials object."""
    return Credentials.from_authorized_user_info(credentials_dict)


def analyze_sentiment(text):
    """Analyze the sentiment of the email text."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a sentiment analysis tool. Analyze the sentiment of the following email text and provide a single word: 'positive', 'neutral', or 'negative'."},
            {"role": "user", "content": text}
        ],
        max_tokens=10
    )
    sentiment = response.choices[0].message.content.strip().lower()
    
    # Normalize to one of the three standard sentiments
    if 'positive' in sentiment:
        return 'positive'
    elif 'negative' in sentiment:
        return 'negative'
    else:
        return 'neutral'


def summarize_email(text):
    """Generate a concise summary of the email text."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an email summarization tool. Provide a concise summary of the following email in 1-2 sentences."},
            {"role": "user", "content": text}
        ],
        max_tokens=100
    )
    return response.choices[0].message.content.strip()


@app.route('/')
def index():
    """Home page route."""
    if 'credentials' in session:
        # User is already authenticated
        return redirect(url_for('list_emails'))
    return render_template('index.html')


@app.route('/login')
def login():
    """Login route that redirects to Google OAuth."""
    flow = Flow.from_client_config(
        client_config=CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=os.getenv('GOOGLE_REDIRECT_URI')
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    session['state'] = state
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    """Callback route for Google OAuth."""
    state = session.get('state')
    
    flow = Flow.from_client_config(
        client_config=CLIENT_CONFIG,
        scopes=SCOPES,
        state=state,
        redirect_uri=os.getenv('GOOGLE_REDIRECT_URI')
    )
    
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('list_emails'))


@app.route('/logout')
def logout():
    """Logout route."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/emails')
def list_emails():
    """Route to list and analyze emails."""
    if 'credentials' not in session:
        return redirect(url_for('login'))
    
    try:
        credentials = dict_to_credentials(session['credentials'])
        gmail_service = build('gmail', 'v1', credentials=credentials)
        
        # Get the user's email address
        profile = gmail_service.users().getProfile(userId='me').execute()
        session['email'] = profile['emailAddress']
        
        # Get latest 10 emails
        results = gmail_service.users().messages().list(
            userId='me',
            maxResults=10,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        processed_emails = []
        
        for message in messages:
            msg = gmail_service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()
            
            # Get email headers
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            # Get email body
            body = ''
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
            
            # Analyze using OpenAI
            summary = summarize_email(body) if body else "Could not extract email content."
            sentiment = analyze_sentiment(body) if body else "neutral"
            
            processed_emails.append({
                'id': message['id'],
                'subject': subject,
                'sender': sender,
                'date': date,
                'summary': summary,
                'sentiment': sentiment
            })
        
        return render_template('emails.html', emails=processed_emails, email=session['email'])
    
    except Exception as e:
        flash(f'Error retrieving emails: {str(e)}')
        return redirect(url_for('index'))


@app.route('/email/<message_id>')
def view_email(message_id):
    """Route to view a specific email."""
    if 'credentials' not in session:
        return redirect(url_for('login'))
    
    try:
        credentials = dict_to_credentials(session['credentials'])
        gmail_service = build('gmail', 'v1', credentials=credentials)
        
        # Get the full email
        msg = gmail_service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        
        # Extract headers
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
        
        # Extract body
        body = ''
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
            body = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
        
        # Analyze
        summary = summarize_email(body) if body else "Could not extract email content."
        sentiment = analyze_sentiment(body) if body else "neutral"
        
        email_data = {
            'id': message_id,
            'subject': subject,
            'sender': sender,
            'date': date,
            'summary': summary,
            'sentiment': sentiment,
            'body': body
        }
        
        return render_template('view_email.html', email=email_data)
    
    except Exception as e:
        flash(f'Error retrieving email: {str(e)}')
        return redirect(url_for('list_emails'))


if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_ENV') == 'development', host='0.0.0.0', port=5000) 