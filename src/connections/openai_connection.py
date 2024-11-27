import os
from dotenv import load_dotenv, set_key
from src.connections.base_connection import BaseConnection
from src.helpers import print_h_bar

class OpenAIConnection(BaseConnection):
    def __init__(self):
        super().__init__()
        self.actions={
            "generate_text": {"prompt": "str"},
        }

    def configure(self):
        """Sets up OpenAI API authentication"""
        print("\n🤖 OPENAI API SETUP")

        # Check if already configured
        if self.is_configured():
            print("\nOpenAI API is already configured.")
            response = input("Do you want to reconfigure? (y/n): ")
            if response.lower() != 'y':
                return

        # Get API key
        print("\n📝 To get your OpenAI API credentials:")
        print("1. Go to https://platform.openai.com/account/api-keys")
        print("2. Create a new project or open an exiting one.")
        print("3. In your project settings, navigate to the API keys section and create a new API key")
        api_key = input("Enter your OpenAI API key: ")

        try:
            # Create .env file if it doesn't exist
            if not os.path.exists('.env'):
                with open('.env', 'w') as f:
                    f.write('')

            # Save API key to .env file
            set_key('.env', 'OPENAI_API_KEY', api_key)

            print("\n✅ OpenAI API configuration successfully saved!")
            print("Your API key has been stored in the .env file.")

        except Exception as e:
            print(f"\n❌ An error occurred during setup: {str(e)}")
            return

    def is_configured(self) -> bool:
        """Checks if OpenAI API key is configured"""
        # TODO: Check if API works
        load_dotenv()
        return bool(os.getenv('OPENAI_API_KEY'))

    def list_actions(self):
        # Tell the user whether the connection is configured or not
        if self.is_configured():
            print("\n✅ OpenAI API is configured. You can use any of its actions.")
        else:
            print("\n❌ OpenAI API is not configured. You must configure a connection in order to use its actions.")

        # List available actions
        print("\nAVAILABLE ACTIONS:")
        for action in self.actions:
            print(f"- {action}: {self.actions[action]}")

    def perform_action(self, action_name, **kwargs):
        # TODO: Implement actions
        pass
