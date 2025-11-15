import os
import webbrowser
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
import threading
import logging
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
TOKEN_FILE = os.getenv('TOKEN_FILE_PATH', '.gcp-saved-tokens.json')
SCOPES = [os.getenv('CALENDAR_SCOPES', 'https://www.googleapis.com/auth/calendar')]
REDIRECT_PORT = int(os.getenv('OAUTH_CALLBACK_PORT', 8080))
REDIRECT_URI = f'http://localhost:{REDIRECT_PORT}/oauth2callback'
# Note: REDIRECT_URI must be registered in your Google Cloud Console OAuth Client settings!

# --- Helper Classes/Functions ---

class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """Handles the OAuth callback request to capture the authorization code."""
    def __init__(self, *args, flow_instance=None, shutdown_event=None, **kwargs):
        self.flow = flow_instance
        self.shutdown_event = shutdown_event
        self.auth_code = None
        self.error = None
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests (the OAuth callback)."""
        query_components = parse_qs(urlparse(self.path).query)
        code = query_components.get('code')
        error = query_components.get('error')

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        if code:
            self.auth_code = code[0]
            logger.info("Authorization code received.")
            self.wfile.write(b'<html><body><h1>Authentication Successful!</h1>')
            self.wfile.write(b'<p>Authorization code received. You can close this window.</p></body></html>')
        elif error:
            self.error = error[0]
            logger.error(f"OAuth Error: {self.error}")
            self.wfile.write(b'<html><body><h1>Authentication Failed</h1>')
            self.wfile.write(f'<p>Error: {self.error}. Please check console.</p></body></html>'.encode())
        else:
            logger.warning("Received callback without code or error.")
            self.wfile.write(b'<html><body><h1>Invalid Callback</h1>')
            self.wfile.write(b'<p>Received an unexpected request.</p></body></html>')

        # Signal the main thread to stop the server
        if self.shutdown_event:
            self.shutdown_event.set()

def start_local_http_server(port, flow, shutdown_event):
    """Starts a temporary local HTTP server to handle the OAuth callback."""
    handler = lambda *args, **kwargs: OAuthCallbackHandler(
        *args, flow_instance=flow, shutdown_event=shutdown_event, **kwargs
    )
    httpd = None
    try:
        httpd = socketserver.TCPServer(("", port), handler)
        logger.info(f"Starting temporary OAuth callback server on port {port}")
        httpd.serve_forever() # This blocks until shutdown is called
    except OSError as e:
        logger.error(f"Failed to start callback server on port {port}: {e}")
        # Signal error if server couldn't start
        if shutdown_event:
             shutdown_event.set() # Also signal to stop waiting
        return None, None # Return None for handler if server failed
    except Exception as e:
        logger.error(f"An unexpected error occurred in the callback server: {e}")
        if shutdown_event:
             shutdown_event.set()
        return None, None
    finally:
        if httpd:
            logger.info("Shutting down OAuth callback server.")
            # httpd.shutdown() # This should be called from another thread or after serve_forever unblocks
            # httpd.server_close() # Clean up the socket
            pass # Shutdown handled by the event

    # This part is tricky because serve_forever blocks.
    # The handler instance is associated with the request, not the server itself long-term.
    # We need a way to get the code back to the main thread. The handler sets it.
    # Let's assume the handler instance associated with the successful callback request is somehow accessible
    # or that the main thread can access the handler's state after shutdown.
    # A more robust way might use queues or other IPC.
    # For now, let's return the handler type, but the instance holding the code is key.
    # We will retrieve the code *after* the server is shut down.
    # The handler instance is tricky to get back here directly after serve_forever.
    # Let's return the server instance, shutdown called externally based on event.
    return httpd, handler # Returning the handler *type* here. Need instance capture.

def get_credentials():
    """Gets valid Google API credentials. Handles loading, refreshing, and the OAuth flow."""
    creds = None

    # Check if mandatory config is present
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        logger.error("Missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET in .env file.")
        raise ValueError("Missing Google OAuth credentials in configuration.")

    # --- 1. Load existing tokens ---
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            logger.info("Loaded credentials from token file.")
        except Exception as e:
            logger.warning(f"Failed to load credentials from {TOKEN_FILE}: {e}. Will attempt re-authentication.")
            creds = None # Ensure creds is None if loading failed

    # --- 2. Refresh or Initiate Flow ---
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Credentials expired. Refreshing...")
            try:
                creds.refresh(Request())
                logger.info("Credentials refreshed successfully.")
            except Exception as e:
                logger.error(f"Failed to refresh credentials: {e}. Need to re-authenticate.")
                creds = None # Force re-authentication
        else:
            logger.info("No valid credentials found or refresh failed. Starting OAuth flow...")
            # Use client_secret dict directly for Flow
            client_config = {
                "installed": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost", REDIRECT_URI] # Add both for flexibility
                }
            }
            try:
                # Use InstalledAppFlow instead of Flow
                logger.info("Attempting authentication using InstalledAppFlow...")
                flow_installed = InstalledAppFlow.from_client_config(
                    client_config=client_config,
                    scopes=SCOPES,
                    redirect_uri=REDIRECT_URI # Ensure this matches console setup
                )
                # This method should handle the server start, browser opening, and code retrieval.
                creds = flow_installed.run_local_server(
                    port=REDIRECT_PORT,
                    authorization_prompt_message="Please visit this URL to authorize:\n{url}",
                    success_message="Authentication successful! You can close this window.",
                    open_browser=True
                )
                logger.info("InstalledAppFlow completed.")

            except Exception as e:
                logger.error(f"Error during InstalledAppFlow execution: {e}", exc_info=True)
                creds = None # Ensure creds is None on error

            if creds:
                # Save the credentials for the next run
                try:
                    with open(TOKEN_FILE, 'w') as token_file:
                        token_file.write(creds.to_json())
                    logger.info(f"Credentials saved successfully to {TOKEN_FILE}")
                except Exception as e:
                    logger.error(f"Failed to save credentials to {TOKEN_FILE}: {e}")
            else:
                logger.error("OAuth flow using InstalledAppFlow did not result in valid credentials.")
                return None

    # --- 3. Final Check ---
    if not creds or not creds.valid:
        logger.error("Failed to obtain valid credentials after all steps.")
        return None

    logger.info("Successfully obtained valid credentials.")
    return creds

# Example usage (can be called from server.py)
if __name__ == '__main__':
    print("Attempting to get Google Calendar credentials...")
    credentials = get_credentials()
    if credentials:
        print("Successfully obtained credentials.")
        print(f"Token URI: {credentials.token_uri}")
        # You can now use these credentials to build the service client
    else:
        print("Failed to obtain credentials.") 