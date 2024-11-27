import json
import os
from requests_oauthlib import OAuth1Session
from src.connections.base_connection import BaseConnection
from src.helpers import print_h_bar

class TwitterConnection(BaseConnection):
    def __init__(self):
        self.api_key = None
        self.api_secret = None
        self.auth_token = None
        self.actions = {
            "get_latest_tweets": {"username": "str", "count": "int"},
            "post_tweet": {"message": "str"},
            # TODO: ADD MORE ACTIONS
        }

    def configure(self):
        print("\n🐦 TWITTER AUTHENTICATION SETUP")

        # Check if config already exists
        if os.path.exists('twitter_config.json'):
            print("\nTwitter configuration already exists.")
            response = input("Do you want to reconfigure? (y/n): ")
            if response.lower() != 'y':
                return

        # Guide user through getting API credentials
        print("\n📝 To get your Twitter API credentials:")
        print("1. Go to https://developer.twitter.com/en/portal/dashboard")
        print("2. Create a new project and app if you haven't already")
        print("3. In your app settings, enable OAuth 1.0a with read and write permissions")
        print("4. Get your API Key (consumer key) and API Key Secret (consumer secret)")
        print_h_bar()

        # Get account details
        print("\nPlease enter your Twitter API credentials:")
        account_id = input("Enter your Twitter username (without @): ")
        consumer_key = input("Enter your API Key (consumer key): ")
        consumer_secret = input("Enter your API Key Secret (consumer secret): ")

        # Initialize config
        config = {
            'accounts': {
                account_id: {
                    'consumer_key': consumer_key,
                    'consumer_secret': consumer_secret
                }
            }
        }

        # Start OAuth process
        print("\nStarting OAuth authentication process...")

        try:
            # Get request token
            request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
            oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

            try:
                fetch_response = oauth.fetch_request_token(request_token_url)
            except ValueError:
                print("\n❌ Error: There may be an issue with your consumer key or secret.")
                return

            resource_owner_key = fetch_response.get("oauth_token")
            resource_owner_secret = fetch_response.get("oauth_token_secret")

            # Get authorization
            base_authorization_url = "https://api.twitter.com/oauth/authorize"
            authorization_url = oauth.authorization_url(base_authorization_url)

            print("\n1. Please visit this URL to authorize the application:")
            print(authorization_url)
            print("\n2. After authorizing, Twitter will give you a PIN code.")
            verifier = input("3. Please enter the PIN code here: ")

            # Get the access token
            access_token_url = "https://api.twitter.com/oauth/access_token"
            oauth = OAuth1Session(
                consumer_key,
                client_secret=consumer_secret,
                resource_owner_key=resource_owner_key,
                resource_owner_secret=resource_owner_secret,
                verifier=verifier,
            )

            oauth_tokens = oauth.fetch_access_token(access_token_url)

            access_token = oauth_tokens.get("oauth_token")
            access_token_secret = oauth_tokens.get("oauth_token_secret")

            # Save the tokens
            config['accounts'][account_id]['access_token'] = access_token
            config['accounts'][account_id]['access_token_secret'] = access_token_secret

            with open('twitter_config.json', 'w') as f:
                json.dump(config, f, indent=4)

            print("\n✅ Twitter authentication successfully set up!")
            print(f"Account '{account_id}' has been configured and saved in the 'twitter_config.json' file.")

        except Exception as e:
            print(f"\n❌ An error occurred during setup: {str(e)}")
            return

    def is_configured(self) -> bool:
        # TODO: Check if API works
        return os.path.exists('twitter_config.json')

    def list_actions(self):
        # TODO: List actions
        pass

    def perform_action(self, action_name, **kwargs):
        # TODO: Implement actions
        pass

