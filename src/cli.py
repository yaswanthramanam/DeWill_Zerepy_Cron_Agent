import sys
from src.agent import ZerePyAgent
class ZerePyCLI:
    def __init__(self):
        print("Initializing...")

        # Initialize blank agent
        self.agent = ZerePyAgent()

        # Start CLI
        self.main_loop()

    def main_loop(self):
        # Send welcome message
        print("--------------------------------------------------------------------")
        print("👋 Hello! Welcome to the ZerePy CLI!")
        print("--------------------------------------------------------------------")
        print("You can use the 'help' command at any time to see what commands you can use.")
        print("You can also use 'help {command}' to get more information about a specific command.")
        print("--------------------------------------------------------------------")

        # MAIN CLI LOOP
        while True:
            # Get user input
            input_string = input("ZerePy-CLI> ")
            input_list = input_string.split()
            command = input_list[0]

            # Run user command
            match command:
                case "exit":
                    # Run exit
                    self.exit()
                case "help":
                    # If additional arguments, get the command the user needs help with
                    help_command = ""
                    if len(input_list) > 1:
                        help_command = input_list[1]

                    # Run help
                    help(help_command)
                case "setup":
                    self.setup()
                    pass
                case "run":
                    # If agent has been initialized, run action through the agent
                    if self.agent.initialized:
                        # If additional arguments, get the action the user wants to run
                        run_action = ""
                        if len(input_list) > 1:
                            run_action = input_list[1]

                        # Run action
                        self.run(run_action)
                case "loop":
                    self.loop()
                case _:
                    print("Unknown command. Try 'help' to see available commands.")

    def help(self, help_command):
        """
        Get help for a specific command, or get a list of all available commands.

        Parameters
        ----------
        help_command : str
            The command for which to display help.

        """
        match help_command:
            # TODO: PROVIDE HELP FOR SPECIFIC COMMANDS
            case "help":
                pass
            case "setup":
                pass
            case "run":
                pass
            case "loop":
                pass
            case "exit":
                pass
            # TODO: PROVIDE HELP FOR ALL COMMANDS
            case "":
                print(f"Help for '{help_command}':")
            case _:
                print("Unknown command. Try 'help' to see available commands.")
        match help_command:
            # TODO: PROVIDE HELP FOR SPECIFIC COMMANDS
            case "help":
                pass
            case "setup":
                pass
            case "run":
                pass
            case "loop":
                pass
            case "exit":
                pass
            # TODO: PROVIDE HELP FOR ALL COMMANDS
            case "":
                print(f"Help for '{help_command}':")
            case _:
                print("Unknown command. Try 'help' to see available commands.")

    def exit(self):
        """
        Exit the ZerePy CLI.

        This function will exit the CLI loop and shut down the CLI.
        It will also perform any cleanup that needs to happen before shutting down.
        """
        # TODO: ANY CLEANUP
        sys.exit()

    def setup(self):
        # TODO: SETUP AGENT
        pass

    def run(self):
        # TODO: RUN A SINGLE AGENT ACTION
        pass

    def loop(self):
        # TODO: RUN AGENT LOOP
        pass

