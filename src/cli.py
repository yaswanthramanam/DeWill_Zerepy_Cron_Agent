import os
import sys
from src.agent import load_agent_from_file

class ZerePyCLI:
    def __init__(self):
        print("Initializing...")

        # TODO: Check if CLI is already setup (.env file exists, API/Auth tokens exist)
        # Add the proper capabilities for the CLI (this will be used to check if an agent's actions are supported)

        # Initialize CLI parameters
        self.setup = False
        self.agent = None
        self.capabilities = []
        self.commands = {
            "help": {
                "command": "help",
                "description": "Displays a list of all available commands, or the help for a specific command.",
                "tips": ["Try 'help' to see available commands.", "Try 'help {command}' to get more information about a specific command (e.g. 'help load-agent')."],
                "func": self.help
            },
            "setup-cli": {
                "command": "setup-cli",
                "description": "Sets up the ZerePy CLI for the first time.",
                "tips": [
                    "If you are planning to use an OpenAI LLM, you will be asked to enter your OpenAI API key.",
                    "If you are planning to use an Anthropic LLM, you will be asked to enter your Anthropic API key.",

                ],
                "func": self.setup_cli
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
                "tips": ["You can list all available agents with the 'list-agents' command.", "You do not need to specify the '.json' extension."],
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
                "description": "Lists all available actions for the current agent.",
                "tips": [
                    "This will also show whether each action is supported by the CLI.",
                    "If an action is supported, you can use it with the 'agent-action' command.",
                    # TODO: FIGURE OUT HOW TO HANDLE UNSUPPORTED ACTIONS
                    "If an action is not supported, you can use ???."
                ],
                "func": self.list_actions
            },

        }

        # Start CLI
        self.main_loop()

    def main_loop(self):
        # Send welcome message
        self.print_h_bar()
        print("👋 Hello! Welcome to the ZerePy CLI!")
        self.print_h_bar()
        print("- You can use the 'help' command at any time to see what commands you can use.")
        print("- You can also use 'help {command}' to get more information about a specific command.")
        self.print_h_bar()

        # If CLI is not setup, ask for API key
        if not self.setup:
            print("⚠️ IF THIS IS YOUR FIRST TIME USING THE CLI: ")
            print("- Please run the 'setup-cli' command to set up the CLI for the first time.")
            print("- You will be asked to enter your OpenAI API key.")
            self.print_h_bar()

        # MAIN CLI LOOP
        while True:
            # PROMPT USER FOR INPUT
            if self.setup:
                if self.agent is None:
                    input_string = input("ZerePy-CLI (no agent) > ")
                else:
                    current_agent_name = self.agent.name
                    input_string = input(f"ZerePy-CLI ({current_agent_name}) > ")
            else:
                input_string = input("ZerePy-CLI (not setup) > ")

            # GET COMMAND FROM INPUT
            input_list = input_string.split()
            command_string = str(input_list[0])

            # RUN COMMAND
            try:
                # Match command string to a supported command
                command_dict = self.commands[command_string]
                command_func = command_dict["func"]

                # Execute command function
                command_func(input_list)
            except IndexError:
                print("\nUnknown command. Try 'help' to see available commands.")
            except KeyError:
                print("\nUnknown command. Try 'help' to see available commands.")
            except Exception as e:
                print(f"\nAn error occurred: {e}")

            # ADD SEPARATOR BEFORE NEXT COMMAND
            self.print_h_bar()

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
        # TODO: ANY CLEANUP
        sys.exit()

    def setup_cli(self, input_list):
        # Check if CLI is already setup
        if self.setup:
            print("\nCLI is already setup. Running the setup again will override your configuration.")
            response = input("Do you want to continue? (y/n) ")
            if response.lower() == "y":
                self.setup = False
            else:
                return

        # TODO:SET UP THE CLI THROUGH INTERACTIVE WIZARD
        self.setup = True

        print("\n✅ SUCCESFULLY SET UP CLI! YOU CAN NOW USE THE CLI TO MANAGE AGENTS!")
        print("You can use the:\n- 'list-agents' command to see all available agents on file\n- 'load-agent' command to load an agent from file\n- 'create-agent' command to create a new agent.")

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

        # Check if action is valid
        if action not in self.agent.actions:
            print("Unknown action. Try 'help' to see available actions.")
            return

        # Run action
        try:
            self.agent.action(input_list[1:])
        except Exception as e:
            print(f"An error occurred while running the action: {e}")

    def agent_loop(self, input_list):
        print("\n🔂 STARTING AGENT LOOP...")
        pass

    def list_agents(self, input_list):
        # List all available agents in the 'agents' directory
        print("\nAVAILABLE AGENTS:")
        for file in os.listdir("agents"):
            if file.endswith(".json"):
                print(f"- {file.removesuffix('.json')}")

    def load_agent(self, input_list):
        # Get agent name from input
        if len(input_list) < 2:
            print("Please specify an agent name.")
            return

        # Load agent
        try:
            self.agent = load_agent_from_file(f"agents/{input_list[1].removesuffix('.json')}.json")
        except FileNotFoundError:
            print("Agent file not found. You can use the 'list-agents' command to see all available agents.")
        except KeyError:
            print("Agent file is missing a required field.")
        except Exception as e:
            print(f"An error occurred while loading the agent: {e}")

        print(f"\n✅ SUCCESSFULLY LOADED AGENT: {self.agent.name}")
        print("Verifying agent actions...")

        # TODO: Verify that the CLI has the right dependencies for the agent

    def create_agent(self, input_list):
        # TODO: CREATE A NEW AGENT THROUGH INTERACTIVE WIZARD
        pass

    def list_actions(self, input_list):
        # List all available actions in the 'actions' directory
        print("\nAVAILABLE ACTIONS:")
        for action in self.agent.actions:
            # TODO: Check whether action is supported by the CLI
            print(f"- {action}")

    def print_h_bar(self):
        print("--------------------------------------------------------------------")
