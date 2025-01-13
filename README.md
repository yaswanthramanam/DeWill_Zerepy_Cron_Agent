# ZerePy

ZerePy is an open-source Python framework designed to let you deploy your own agents on X, powered by OpenAI/Anthropic/EternalAI LLMs.

ZerePy is built from a modularized version of the Zerebro backend. With ZerePy, you can launch your own agent with
similar core functionality as Zerebro. For creative outputs, you'll need to fine-tune your own model.

## Features

### Core Platform

- CLI interface for managing agents
- Modular connection system
- Blockchain integration with Solana
- HTTP server mode with REST API

### Social Platform Integrations

- Twitter/X
- Farcaster
- Echochambers

### Language Model Support

- OpenAI
- Anthropic
- EternalAI
- Ollama
- Hyperbolic
- Galadriel

## Quickstart

The quickest way to start using ZerePy is to use our Replit template:

https://replit.com/@blormdev/ZerePy?v=1

1. Fork the template (you will need you own Replit account)
2. Click the run button on top
3. Voila! your CLI should be ready to use, you can jump to the configuration section

## Requirements

System:

- Python 3.10 or higher
- Poetry 1.5 or higher

Environment Variables:

- LLM: make an account and grab an API key (at least one)
  - OpenAI: https://platform.openai.com/api-keys
  - Anthropic: https://console.anthropic.com/account/keys
  - EternalAI: https://eternalai.oerg/api
  - Hyperbolic: https://app.hyperbolic.xyz
  - Galadriel: https://dashboard.galadriel.com
- Social (based on your needs):
  - X API: https://developer.x.com/en/docs/authentication/oauth-1-0a/api-key-and-secret
  - Farcaster: Warpcast recovery phrase
  - Echochambers: API key and endpoint
- On-chain Integration:
  - Solana: private key (in base58 format) for transactions
  - RPC URL (defaults to public endpoints)

## Installation

1. First, install Poetry for dependency management if you haven't already:

Follow the steps here to use the official installation: https://python-poetry.org/docs/#installing-with-the-official-installer

2. Clone the repository:

```bash
git clone https://github.com/blorm-network/ZerePy.git
```

3. Go to the `zerepy` directory:

```bash
cd zerepy
```

4. Install dependencies:

For CLI mode only:

```bash
poetry install --no-root
```

For server mode support:

```bash
poetry install --extras server --no-root
```

## Usage

### CLI Mode

1. Activate the virtual environment:

```bash
poetry shell
```

2. Run the application:

```bash
poetry run python main.py
```

### Server Mode

ZerePy can also run as an HTTP server, providing a REST API for remote agent management and automation. This is particularly useful for integration with other services or building custom UIs.

1. Start the server:

```bash
poetry run python main.py --server
```

Optional parameters:

--host: Server host (default: 0.0.0.0)
--port: Server port (default: 8000)

2. Using the Python Client:

```python
from src.client import ZerePyClient

# Initialize client
client = ZerePyClient("http://localhost:8000")

# Check server status
status = client.get_status()

# List available agents
agents = client.list_agents()

# Load an agent
client.load_agent("example")

# List connections
connections = client.list_connections()

# Perform an action
result = client.perform_action("twitter", "post-tweet", ["Hello from ZerePy!"])

# Start/stop agent loop
client.start_agent()
client.stop_agent()
```

3. Testing with cURL:

Check server status:

```bash
curl http://localhost:8000/
```

## Configure connections & launch an agent

### Note: configuring connections in server mode will consist of preparing the appropriate portinos of the .env file, as we will not have step-by-step cli config method

1. Configure your desired connections:

```

configure-connection twitter # For Twitter/X integration
configure-connection openai # For OpenAI
configure-connection anthropic # For Anthropic
configure-connection farcaster # For Farcaster
configure-connection eternalai # For EternalAI
configure-connection galadriel # For Galadriel
configure-connection solana # For Solana

```

2. Use `list-connections` to see all available connections and their status

3. Load your agent (usually one is loaded by default, which can be set using the CLI or in agents/general.json):

```

load-agent example

```

4. Start your agent:

```

start

```

## Platform Features

### Solana

- Transfer SOL and SPL tokens
- Swap tokens using Jupiter
- Check token balances
- Stake SOL
- Monitor network TPS
- Query token information
- Request testnet/devnet funds

### Twitter/X

- Post tweets from prompts
- Read timeline with configurable count
- Reply to tweets in timeline
- Like tweets in timeline

### Farcaster

- Post casts
- Reply to casts
- Like and requote casts
- Read timeline
- Get cast replies

### Echochambers

- Post new messages to rooms
- Reply to messages based on room context
- Read room history
- Get room information and topics

## Create your own agent

The secret to having a good output from the agent is to provide as much detail as possible in the configuration file. Craft a story and a context for the agent, and pick very good examples of tweets to include.

If you want to take it a step further, you can fine tune your own model: https://platform.openai.com/docs/guides/fine-tuning.

Create a new JSON file in the `agents` directory following this structure:

```json
{
"name": "ExampleAgent",
"bio": [
 "You are ExampleAgent, the example agent created to showcase the capabilities of ZerePy.",
 "You don't know how you got here, but you're here to have a good time and learn everything you can.",
 "You are naturally curious, and ask a lot of questions."
],
"traits": ["Curious", "Creative", "Innovative", "Funny"],
"examples": ["This is an example tweet.", "This is another example tweet."],
"example_accounts" : ["X_username_to_use_for_tweet_examples"]
"loop_delay": 900,
"config": [
 {
   "name": "twitter",
   "timeline_read_count": 10,
   "own_tweet_replies_count": 2,
   "tweet_interval": 5400
 },
 {
   "name": "farcaster",
   "timeline_read_count": 10,
   "cast_interval": 60
 },
 {
   "name": "openai",
   "model": "gpt-3.5-turbo"
 },
 {
   "name": "anthropic",
   "model": "claude-3-5-sonnet-20241022"
 },
 {
   "name": "eternalai",
   "model": "NousResearch/Hermes-3-Llama-3.1-70B-FP8",
   "chain_id": "45762"
 },
 {
   "name": "solana",
   "rpc": "https://api.mainnet-beta.solana.com"
 },
 {
   "name": "ollama",
   "base_url": "http://localhost:11434",
   "model": "llama3.2"
 },
 {
   "name": "hyperbolic",
   "model": "meta-llama/Meta-Llama-3-70B-Instruct"
 },
 {
   "name": "galadriel",
   "model": "gpt-3.5-turbo"
 }
],
"tasks": [
 { "name": "post-tweet", "weight": 1 },
 { "name": "reply-to-tweet", "weight": 1 },
 { "name": "like-tweet", "weight": 1 }
],
"use_time_based_weights": false,
"time_based_multipliers": {
 "tweet_night_multiplier": 0.4,
 "engagement_day_multiplier": 1.5
}
}
```

## Available Commands

Use `help` in the CLI to see all available commands. Key commands include:

- `list-agents`: Show available agents
- `load-agent`: Load a specific agent
- `agent-loop`: Start autonomous behavior
- `agent-action`: Execute single action
- `list-connections`: Show available connections
- `list-actions`: Show available actions for a connection
- `configure-connection`: Set up a new connection
- `chat`: Start interactive chat with agent
- `clear`: Clear the terminal screen

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=blorm-network/ZerePy&type=Date)](https://star-history.com/#blorm-network/ZerePy&Date)

---

Made with ♥ @Blorm.xyz
