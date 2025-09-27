"""Google authentication handling for Sheets API access."""

import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-untyped]
import gspread

logger = logging.getLogger(__name__)


class GoogleAuthenticator:
    """Handles Google authentication for Sheets API access."""

    # Google Sheets API scope
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, credentials_path: str | Path, auth_type: str = "service_account"):
        """Initialize authenticator.

        Args:
            credentials_path: Path to credentials file
            auth_type: Type of authentication ('service_account' or 'oauth')
        """
        self.credentials_path = Path(credentials_path)
        self.auth_type = auth_type
        self._credentials: Credentials | ServiceAccountCredentials | None = None

    def authenticate(self) -> gspread.Client:
        """Authenticate and return gspread client.

        Returns:
            Authenticated gspread client

        Raises:
            FileNotFoundError: If credentials file not found
            ValueError: If invalid auth_type
            Exception: If authentication fails
        """
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")

        try:
            if self.auth_type == "service_account":
                return self._authenticate_service_account()
            elif self.auth_type == "oauth":
                return self._authenticate_oauth()
            else:
                raise ValueError(f"Invalid auth_type: {self.auth_type}")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def _authenticate_service_account(self) -> gspread.Client:
        """Authenticate using service account credentials.

        Returns:
            Authenticated gspread client
        """
        logger.info("Authenticating with service account")

        try:
            self._credentials = ServiceAccountCredentials.from_service_account_file(
                str(self.credentials_path), scopes=self.SCOPES
            )
            client = gspread.authorize(self._credentials)
            logger.info("Service account authentication successful")
            return client

        except Exception as e:
            logger.error(f"Service account authentication failed: {e}")
            raise

    def _authenticate_oauth(self) -> gspread.Client:
        """Authenticate using OAuth flow.

        Returns:
            Authenticated gspread client
        """
        logger.info("Authenticating with OAuth")

        try:
            # Token file for storing user credentials
            token_path = self.credentials_path.parent / "token.json"

            creds = None
            # Load existing token if available
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), self.SCOPES)

            # If no valid credentials available, initiate OAuth flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired OAuth token")
                    creds.refresh(Request())
                else:
                    logger.info("Starting OAuth flow")
                    flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), self.SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save credentials for next run
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
                logger.info(f"OAuth token saved to {token_path}")

            self._credentials = creds
            client = gspread.authorize(creds)
            logger.info("OAuth authentication successful")
            return client

        except Exception as e:
            logger.error(f"OAuth authentication failed: {e}")
            raise

    def test_connection(self) -> bool:
        """Test the authentication by attempting to list spreadsheets.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            client = self.authenticate()
            # Try to access user's spreadsheets (this will fail gracefully if no access)
            client.list_permissions("test")  # This will raise an exception for invalid sheet
            return True
        except Exception as e:
            # This is expected for invalid sheet ID, but connection works if we can authenticate
            if "permission" in str(e).lower() or "not found" in str(e).lower():
                logger.info("Authentication successful (expected permission error for test sheet)")
                return True
            logger.error(f"Connection test failed: {e}")
            return False

    @property
    def credentials(self) -> Credentials | ServiceAccountCredentials | None:
        """Get current credentials object."""
        return self._credentials
