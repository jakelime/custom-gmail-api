import logging
import os
from pathlib import Path
from typing import Optional

import httplib2
from googleapiclient import errors as google_api_errors
from googleapiclient.discovery import build
from oauth2client.client import (
    Credentials,  # Needed for type hinting/usage in comments
    FlowExchangeError,
    flow_from_clientsecrets,
)


# Path to credentials.json which should contain a JSON document such as:
#   {
#     "web": {
#       "client_id": "[[YOUR_CLIENT_ID]]",
#       "client_secret": "[[YOUR_CLIENT_SECRET]]",
#       "redirect_uris": [],
#       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#       "token_uri": "https://accounts.google.com/o/oauth2/token"
#     }
#   }
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


CLIENTSECRETS_LOCATION = get_client_secrets_file()
REDIRECT_URI = "<YOUR_REGISTERED_REDIRECT_URI>"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    # Add other requested scopes.
]


class GetCredentialsException(Exception):
    """Error raised when an error occurred while retrieving credentials.

    Attributes:
      authorization_url: Authorization URL to redirect the user to in order to
                        request offline access.
    """

    def __init__(self, authorization_url):
        """Construct a GetCredentialsException."""
        super().__init__(f"Authorization URL: {authorization_url}")
        self.authorization_url = authorization_url


class CodeExchangeException(GetCredentialsException):
    """Error raised when a code exchange has failed."""

    pass


class NoRefreshTokenException(GetCredentialsException):
    """Error raised when no refresh token has been found."""

    pass


class NoUserIdException(Exception):
    """Error raised when no user ID could be retrieved."""

    pass


def get_stored_credentials(user_id):
    """Retrieved stored credentials for the provided user ID.

    Args:
      user_id: User's ID.

    Returns:
      Stored oauth2client.client.OAuth2Credentials if found, None otherwise.

    Raises:
      NotImplementedError: This function has not been implemented.
    """
    # TODO: Implement this function to work with your database.
    #       To instantiate an OAuth2Credentials instance from a Json
    #       representation, use the oauth2client.client.Credentials.new_from_json
    #       class method. (oauth2client.client.Credentials needs to be imported)
    #       Example:
    #       from oauth2client.client import Credentials
    #       json_creds = load_from_db(user_id)
    #       if json_creds:
    #           return Credentials.new_from_json(json_creds)
    #       return None
    raise NotImplementedError()


def store_credentials(user_id, credentials):
    """Store OAuth 2.0 credentials in the application's database.

    This function stores the provided OAuth 2.0 credentials using the user ID as
    key.

    Args:
      user_id: User's ID.
      credentials: OAuth 2.0 credentials to store.

    Raises:
      NotImplementedError: This function has not been implemented.
    """
    # TODO: Implement this function to work with your database.
    #       To retrieve a Json representation of the credentials instance, call the
    #       credentials.to_json() method.
    #       Example:
    #       save_to_db(user_id, credentials.to_json())
    raise NotImplementedError()


def exchange_code(authorization_code):
    """Exchange an authorization code for OAuth 2.0 credentials.

    Args:
      authorization_code: Authorization code to exchange for OAuth 2.0
                          credentials.

    Returns:
      oauth2client.client.OAuth2Credentials instance.

    Raises:
      CodeExchangeException: an error occurred.
    """
    flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, " ".join(SCOPES))
    flow.redirect_uri = REDIRECT_URI
    try:
        credentials = flow.step2_exchange(authorization_code)
        return credentials
    except FlowExchangeError as error:
        logging.error("An error occurred: %s", error)
        raise CodeExchangeException(None)


def get_user_info(credentials):
    """Send a request to the UserInfo API to retrieve the user's information.

    Args:
      credentials: oauth2client.client.OAuth2Credentials instance to authorize the
                request.

    Returns:
      User information as a dict.
    """
    user_info_service = build(
        serviceName="oauth2", version="v2", http=credentials.authorize(httplib2.Http())
    )
    user_info = None
    try:
        user_info = user_info_service.userinfo().get().execute()
    except google_api_errors.HttpError as e:
        logging.error("An error occurred: %s", e)
    if user_info and user_info.get("id"):
        return user_info
    else:
        raise NoUserIdException()


def get_authorization_url(email_address, state):
    """Retrieve the authorization URL.

    Args:
      email_address: User's e-mail address.
      state: State for the authorization URL.

    Returns:
      Authorization URL to redirect the user to.
    """
    flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, " ".join(SCOPES))
    flow.params["access_type"] = "offline"
    flow.params["approval_prompt"] = "force"
    flow.params["user_id"] = email_address
    flow.params["state"] = state
    # The step1_get_authorize_url method uses the flow.redirect_uri attribute.
    flow.redirect_uri = REDIRECT_URI
    return flow.step1_get_authorize_url()


def get_credentials(authorization_code, state):
    """Retrieve credentials using the provided authorization code.

    This function exchanges the authorization code for an access token and queries
    the UserInfo API to retrieve the user's e-mail address.

    If a refresh token has been retrieved along with an access token, it is stored
    in the application database using the user's e-mail address as key.

    If no refresh token has been retrieved, the function checks in the application
    database for one and returns it if found or raises a NoRefreshTokenException
    with the authorization URL to redirect the user to.

    Args:
      authorization_code: Authorization code to use to retrieve an access token.
      state: State to set to the authorization URL in case of error.

    Returns:
      oauth2client.client.OAuth2Credentials instance containing an access and
      refresh token.

    Raises:
      CodeExchangeError: Could not exchange the authorization code.
      NoRefreshTokenException: No refresh token could be retrieved from the
                            available sources.
    """
    email_address = ""
    try:
        credentials = exchange_code(authorization_code)
        user_info = get_user_info(
            credentials
        )  # Can raise NoUserIdException or google_api_errors.HttpError
        email_address = user_info.get("email")
        user_id = user_info.get("id")
        if credentials.refresh_token is not None:
            store_credentials(user_id, credentials)
            return credentials
        else:
            credentials = get_stored_credentials(user_id)
            if credentials and credentials.refresh_token is not None:
                return credentials
    except CodeExchangeException as error:
        logging.error("An error occurred during code exchange.")
        # Drive apps should try to retrieve the user and credentials for the current
        # session.
        # If none is available, redirect the user to the authorization URL.
        error.authorization_url = get_authorization_url(email_address, state)
        raise error
    except NoUserIdException:
        logging.error("No user ID could be retrieved.")
    # No refresh token has been retrieved.
    authorization_url = get_authorization_url(email_address, state)
    raise NoRefreshTokenException(authorization_url)


def main():
    get_credentials(os.environ.get("apikey", ""), "abc")


if __name__ == "__main__":
    try:
        main()
    except GetCredentialsException as e:
        print(f"Error: {e}")
        print(f"Authorization URL: {e.authorization_url}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
