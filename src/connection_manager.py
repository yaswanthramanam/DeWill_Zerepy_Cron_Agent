import os
from dotenv import load_dotenv
from src.connections.openai_connection import OpenAIConnection
from src.connections.twitter_connection import TwitterConnection

class ConnectionManager:
    def __init__(self):
        self.connections = {
            'twitter': TwitterConnection(),
            'openai': OpenAIConnection(),
        }

    def configure_connection(self, connection_string):
        try:
            # Match connection string to a supported connection
            connection = self.connections[connection_string]
            # Run configuration function
            connection.configure()
            # If configuration was successful, add connection to list
            if connection.is_configured():
                print(f"\n✅ SUCCESSFULLY CONFIGURED CONNECTION: {connection_string}")
            else:
                print(f"\n❌ ERROR CONFIGURING CONNECTION: {connection_string}")
        except KeyError:
            print("\nUnknown connection. Try 'list-connections' to see all supported connections.")
        except Exception as e:
            print(f"\nAn error occurred: {e}")

    def list_connections(self):
        print("\nAVAILABLE CONNECTIONS:")
        for connection_key, connection in self.connections.items():
            if connection.is_configured():
                print(f"- {connection_key} : ✅ Configured")
            else:
                print(f"- {connection_key} : ❌ Not Configured")

    def list_actions(self, connection_string):
        try:
            # Match connection string to a supported connection
            connection = self.connections[connection_string]

            # Tell the user whether the connection is configured or not
            if connection.is_configured():
                print(f"\n✅ {connection_string} is configured. You can use any of its actions.")
            else:
                print(f"\n❌ {connection_string} is not configured. You must configure a connection in order to use its actions.")

            # List available actions
            print("\nAVAILABLE ACTIONS:")
            for action in connection.actions:
                print(f"- {action}: {connection.actions[action]}")
        except KeyError:
            print("\nUnknown connection. Try 'list-connections' to see all supported connections.")
        except Exception as e:
            print(f"\nAn error occurred: {e}")

    def is_action_supported(self, action):
        # TODO: Check if action is supported
        pass