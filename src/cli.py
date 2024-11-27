import os
import sys
from src.agent import load_agent_from_file
from src.helpers import print_h_bar
import json
from requests_oauthlib import OAuth1Session
import logging
from dotenv import load_dotenv, set_key
from src.connection_manager import ConnectionManager


class ZerePyCLI:
    def __init__(self):

        # Initialize CLI parameters
        self.agent = None
        self.connection_manager = ConnectionManager()
        self.commands = {
            "help": {
                "command": "help",
                "description": "Displays a list of all available commands, or the help for a specific command.",
                "tips": ["Try 'help' to see available commands.",
                         "Try 'help {command}' to get more information about a specific command (e.g. 'help load-agent')."],
                "func": self.help
            },
            "agent-action": {
                "command": "agent-action",
                "description": "Runs a single agent action.",
                "tips": [],
                "func": self.agent_action
            },
            "agent-loop": {
                "command": "agent-loop",
                "description": "Starts the current agent's autonomous behavior loop.",
                "tips": [],
                "func": self.agent_loop
            },
            "list-agents": {
                "command": "list-agents",
                "description": "Lists all available agents you have on file. These can be found in the 'agents' directory.",
                "tips": ["You can load any available agent with the 'load-agent' command."],
                "func": self.list_agents
            },
            "load-agent": {
                "command": "load-agent",
                "description": "Loads an agent from a file.",
                "tips": ["You can list all available agents with the 'list-agents' command.",
                         "You do not need to specify the '.json' extension."],
                "func": self.load_agent
            },
            "exit": {
                "command": "exit",
                "description": "Exits the ZerePy CLI.",
                "tips": [],
                "func": self.exit
            },
            "create-agent": {
                "command": "create-agent",
                "description": "Creates a new agent.",
                "tips": [],
                "func": self.create_agent
            },
            "list-actions": {
                "command": "list-actions",
                "description": "Lists all available actions for the given connection.",
                "tips": [
                    "You must give the name of a connection like so: 'list-actions twitter'.",
                    "You can use the 'list-connections' command to see all available connections.",
                    "This command will also tell you if the connection is configured or not."
                ],
                "func": self.list_actions
            },
            "configure-connection": {
                "command": "configure-connection",
                "description": "Sets up the given connection so that your agents can use the API.",
                "tips": [
                    "Each connection requires a different set of credentials. You will be prompted for the necessary credentials.",
                    "You must give the name of a connection like so: 'configure-connection twitter'.",
                    "You can use the 'list-connections' command to see all available connections.",
                    "Your credentials will be saved to local files for future use. That way you only have to set up each connection once."
                ],
                "func": self.configure_connection
            },
            "list-connections": {
                "command": "list-connections",
                "description": "Lists all available connections (configured or not).",
                "tips": [],
                "func": self.list_connections
            }
        }

        # Start CLI
        self.main_loop()

    def main_loop(self):
        # Send welcome message first
        print_h_bar()
        print("👋 Hello! Welcome to the ZerePy CLI!")
        # Check connections status once at startup
        self.list_connections([])
        print_h_bar()

        # MAIN CLI LOOP
        while True:
            # PROMPT USER FOR INPUT
            if self.agent is None:
                input_string = input("ZerePy-CLI (no agent) > ")
            else:
                current_agent_name = self.agent.name
                input_string = input(f"ZerePy-CLI ({current_agent_name}) > ")

            # GET COMMAND FROM INPUT
            input_list = input_string.split()
            if not input_list:  # Handle empty input
                continue
            command_string = str(input_list[0])

            # RUN COMMAND
            try:
                # Match command string to a supported command
                command_dict = self.commands[command_string]
                command_func = command_dict["func"]
                # Run command function
                command_func(input_list)
            except KeyError:
                print("\nUnknown command. Try 'help' to see available commands.")
            except Exception as e:
                print(f"\nAn error occurred: {e}")

            # ADD SEPARATOR BEFORE NEXT COMMAND
            print_h_bar()

    def help(self, input_list):
        # GET HELP ARGUMENT STRING
        help_arg_string = ""
        if len(input_list) > 1:
            help_arg_string = str(input_list[1])

        if help_arg_string != "":
            # SPECIFIC COMMAND HELP
            try:
                # Match command string to a supported command
                command_dict = self.commands[help_arg_string]
                command_description = command_dict["description"]

                # Print help for command
                print(f"\nHELP FOR '{help_arg_string}':")
                print(command_description)
                for tip in command_dict["tips"]:
                    print(f"- {tip}")
            except IndexError:
                print("Unknown command. Try 'help' to see available commands.")
            except KeyError:
                print("Unknown command. Try 'help' to see available commands.")
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            # GENERAL HELP
            # Print list of available commands
            print("\nAVAILABLE CLI COMMANDS:")
            for command in self.commands:
                print(f"- {command}")

            # Print current agent (or say there is currently no initialized agent)
            if self.agent is None:
                print("\nCURRENT AGENT: None")
            else:
                print(f"\nCURRENT AGENT: {self.agent.name}")

            # Print docs link
            # TODO: Add docs link
            print("\nDOCS: https://zerepy.com/docs")

    def exit(self, input_list):
        sys.exit()

    def agent_action(self, input_list):
        # Check if agent is loaded
        if self.agent is None:
            print("No agent is currently loaded. You can use the 'load-agent' command to load an agent.")
            return

        # Check if user has specified an action
        if len(input_list) < 2:
            print("Please specify an action.")
            return

        # Get action from input
        action = input_list[1]

        # Run action
        try:
            self.agent.perform_action(action, input_list)
        except Exception as e:
            print(f"An error occurred while running the action: {e}")

    def agent_loop(self, input_list):
        print("\n🔂 STARTING AGENT LOOP...")
        # TODO: IMPLEMENT AGENT LOOP
        pass

    def list_agents(self, input_list):
        # List all available agents in the 'agents' directory
        print("\nAVAILABLE AGENTS:")
        agents = 0
        for file in os.listdir("agents"):
            if file.endswith(".json"):
                print(f"- {file.removesuffix('.json')}")
                agents += 1

        if agents == 0:
            print("No agents found. You can use the 'create-agent' command to create a new agent.")

    def load_agent(self, input_list):
        # Get agent name from input
        if len(input_list) < 2:
            print("Please specify an agent name. You can see all available agent names with the 'list-agents' command.")
            return

        # Load agent
        try:
            self.agent = load_agent_from_file(
                agent_path=f"agents/{input_list[1].removesuffix('.json')}.json",
                connection_manager=self.connection_manager
            )
        except FileNotFoundError:
            print("Agent file not found. You can use the 'list-agents' command to see all available agents.")
        except KeyError:
            print("Agent file is missing a required field.")
        except Exception as e:
            print(f"An error occurred while loading the agent: {e}")

        print(f"\n✅ SUCCESSFULLY LOADED AGENT: {self.agent.name}")

    def create_agent(self, input_list):
        # TODO: CREATE A NEW AGENT THROUGH INTERACTIVE WIZARD
        pass

    def list_actions(self, input_list):
        if len(input_list) < 2:
            print("\nPlease specify a connection. You can use the 'list-connections' command to see all supported connections.")
            return

        # Get connection name from input
        connection_string = input_list[1]

        # Configure connection
        self.connection_manager.list_actions(connection_string=connection_string)

    def list_connections(self, input_list):
        self.connection_manager.list_connections()

    def configure_connection(self, input_list):
        if len(input_list) < 2:
            print("\nPlease specify a connection to configure. You can use the 'list-connections' command to see all supported connections.")
            return

        # Get connection name from input
        connection_string = input_list[1]

        # Configure connection
        self.connection_manager.configure_connection(connection_string=connection_string)