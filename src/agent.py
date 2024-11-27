import json
from src.connection_manager import ConnectionManager


class ZerePyAgent:
    def __init__(self, name, model, connection_manager, bio, moderated=True):
        self.name = name
        self.model = model
        self.connection_manager = connection_manager
        self.bio = bio
        self.moderated = moderated

    def loop(self):
        # TODO: RUN AGENT LOOP
        pass

    def perform_action(self, action, **kwargs):
        # TODO: RUN A SINGLE AGENT ACTION
        pass

    def to_dict(self):
        return {
            "name": self.name,
            "model": self.model,
            "bio": self.bio,
            "moderated": self.moderated
        }


def load_agent_from_file(agent_path: str, connection_manager: ConnectionManager) -> ZerePyAgent:
    try:
        # Get agent fields from json file
        agent_dict = json.load(open(agent_path, "r"))

        # Create agent object
        agent = ZerePyAgent(
            name=agent_dict["name"],
            model=agent_dict["model"],
            connection_manager=connection_manager,
            bio=agent_dict["bio"],
            moderated=agent_dict["moderated"]
        )
    except FileNotFoundError:
        raise FileNotFoundError(f"Agent file not found at path: {agent_path}")
    except KeyError:
        raise KeyError(f"Agent file is missing a required field.")
    except Exception as e:
        raise Exception(f"An error occurred while loading the agent: {e}")
    return agent


def create_agent_file_from_dict(agent_dict: dict):
    try:
        # Create agent file
        with open(f"agents/{agent_dict['name']}.json", "w") as file:
            # Save agent dict to json file
            json.dump(agent_dict, file, indent=4)
    except Exception as e:
        raise Exception(f"An error occurred while creating the agent file: {e}")
