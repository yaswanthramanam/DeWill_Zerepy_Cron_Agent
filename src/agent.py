import json


class ZerePyAgent:
    def __init__(self, name, llm_provider, llm_model, actions, bio, moderated=True):
        # REQUIRED PARAMETERS
        self.name = name
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.actions = actions
        self.bio = bio
        self.moderated = moderated

        # OPTIONAL PARAMETERS

    def loop(self):
        # TODO: RUN AGENT LOOP
        pass

    def action(self):
        # TODO: RUN A SINGLE AGENT ACTION
        pass


def load_agent_from_file(agent_path: str) -> ZerePyAgent:
    try:
        # Get agent fields from json file
        agent_dict = json.load(open(agent_path, "r"))

        # Create agent object
        agent = ZerePyAgent(
            name=agent_dict["name"],
            llm_provider=agent_dict["llm_provider"],
            llm_model=agent_dict["llm_model"],
            dependencies=agent_dict["dependencies"],
            actions=agent_dict["actions"],
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
        # Save agent dict to json file
        json.dump(agent_dict, open(f"agents/{agent_dict['name']}.json", "w"), indent=4)
    except Exception as e:
        raise Exception(f"An error occurred while creating the agent file: {e}")
