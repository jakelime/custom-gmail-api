from __future__ import print_function

import base64
import os
import pickle
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()


def get_client_secrets_file(creds_folder_name: str = "creds") -> Optional[Path]:
    """Returns the path to the client secrets file."""
    creds_dir = Path.cwd() / creds_folder_name
    cred_files = list(creds_dir.glob("*.json"))
    cred_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    cred_file = cred_files[0] if cred_files else None
    if cred_file is not None and cred_file.is_file():
        return cred_file
    else:
        return None


def google_auth_protocol(
    creds_folder_name: str = "creds",
    scopes=["https://www.googleapis.com/auth/gmail.send"],
):
    # If modifying these scopes, delete the file token.pickle.

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = Path.cwd() / creds_folder_name / "token.pickle"
    if token_path.is_file():
        with open(token_path, "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                get_client_secrets_file(creds_folder_name), scopes
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)
    return creds


def gmail_send_message(creds, email_target: str):
    if not email_target:
        raise ValueError("Email target must be provided")

    try:
        service = build("gmail", "v1", credentials=creds)

        message = EmailMessage()
        message.set_content("This is automated draft mail")
        message["To"] = email_target
        message["Subject"] = "Automated draft"
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}

        sent_message = (
            service.users().messages().send(userId="me", body=create_message).execute()
        )
        print(f'email sent to {email_target}. Message Id: {sent_message["id"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        sent_message = None
    return sent_message


def main():
    """Shows basic usage of the PostmasterTools v1beta1 API.
    Prints the visible domains on user's domain dashboard in https://postmaster.google.com/managedomains.
    """
    creds = google_auth_protocol(creds_folder_name="creds")
    gmail_send_message(creds, os.environ.get("send_email_target", ""))


if __name__ == "__main__":
    main()
