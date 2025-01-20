import logging
import os
from typing import Dict, Any
from dotenv import load_dotenv, set_key
from xai import xAI  # Hypothetical import for xAI's API
from src.connections.base_connection import BaseConnection, Action, ActionParameter

logger = logging.getLogger("connections.xai_connection")

class xAIConnectionError(Exception):
    """Base exception for xAI connection errors"""
    pass

class xAIConfigurationError(xAIConnectionError):
    """Raised when there are configuration/credential issues with xAI"""
    pass

class xAIAPIError(xAIConnectionError):
    """Raised when xAI API requests fail"""
    pass

class xAIConnection(BaseConnection):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._client = None

    @property
    def is_llm_provider(self) -> bool:
        return True

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate xAI configuration from JSON"""
        required_fields = ["model"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")
            
        if not isinstance(config["model"], str):
            raise ValueError("model must be a string")
            
        return config

    def register_actions(self) -> None:
        """Register available xAI actions"""
        self.actions = {
            "generate-text": Action(
                name="generate-text",
                parameters=[
                    ActionParameter("prompt", True, str, "The input prompt for text generation"),
                    ActionParameter("system_prompt", False, str, "System prompt to guide the model"),
                    ActionParameter("model", False, str, "Model to use for generation")
                ],
                description="Generate text using xAI models"
            ),
            "check-model": Action(
                name="check-model",
                parameters=[
                    ActionParameter("model", True, str, "Model name to check availability")
                ],
                description="Check if a specific model is available"
            ),
            "list-models": Action(
                name="list-models",
                parameters=[],
                description="List all available xAI models"
            )
        }

    def _get_client(self) -> xAI:
        """Get or create xAI client"""
        if not self._client:
            api_key = os.getenv("XAI_API_KEY")
            if not api_key:
                raise xAIConfigurationError("xAI API key not found in environment")
            self._client = xAI(api_key=api_key)
        return self._client

    def configure(self) -> bool:
        """Sets up xAI API authentication"""
        logger.info("\n🤖 xAI API SETUP")

        if self.is_configured():
            logger.info("\n xAI API is already configured.")
            response = input("Do you want to reconfigure? (y/n): ")
            if response.lower() != 'y':
                return True

        logger.info("\n📝 To get your xAI API credentials:")
        logger.info("1. Go to the xAI developer portal (assuming one exists)")
        logger.info("2. Create a new API key for your project.")
        
        api_key = input("\nEnter your xAI API key: ")

        try:
            if not os.path.exists('.env'):
                with open('.env', 'w') as f:
                    f.write('')

            set_key('.env', 'XAI_API_KEY', api_key)
            
            # Validate the API key by trying to list models
            client = xAI(api_key=api_key)
            client.models.list()

            logger.info("\n✅ xAI API configuration successfully saved!")
            logger.info("Your API key has been stored in the .env file.")
            return True

        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            return False

    def is_configured(self, verbose = False) -> bool:
        """Check if xAI API key is configured and valid"""
        try:
            load_dotenv()
            api_key = os.getenv('XAI_API_KEY')
            if not api_key:
                return False

            client = xAI(api_key=api_key)
            client.models.list()
            return True
            
        except Exception as e:
            if verbose:
                logger.debug(f"Configuration check failed: {e}")
            return False

    def generate_text(self, prompt: str, system_prompt: str = None, model: str = None, **kwargs) -> str:
        """Generate text using xAI models"""
        try:
            client = self._get_client()
            
            # Use configured model if none provided
            if not model:
                model = self.config["model"]

            # Assuming xAI's API has a similar structure to others for text generation
            response = client.generate(
                model=model,
                prompt=prompt,
                system_prompt=system_prompt if system_prompt else ""
            )
            return response.text
            
        except Exception as e:
            raise xAIAPIError(f"Text generation failed: {e}")

    def check_model(self, model: str, **kwargs) -> bool:
        """Check if a specific model is available"""
        try:
            client = self._get_client()
            try:
                client.models.retrieve(model=model)
                return True
            except Exception:
                return False
        except Exception as e:
            raise xAIAPIError(f"Model check failed: {e}")

    def list_models(self, **kwargs) -> None:
        """List all available xAI models"""
        try:
            client = self._get_client()
            models = client.models.list()
            
            logger.info("\nGROK MODELS:")
            for i, model in enumerate(models):
                logger.info(f"{i+1}. {model.id}")
                
        except Exception as e:
            raise xAIAPIError(f"Listing models failed: {e}")

    def perform_action(self, action_name: str, kwargs) -> Any:
        """Execute an action with validation"""
        if action_name not in self.actions:
            raise KeyError(f"Unknown action: {action_name}")

        action = self.actions[action_name]
        errors = action.validate_params(kwargs)
        if errors:
            raise ValueError(f"Invalid parameters: {', '.join(errors)}")

        # Call the appropriate method based on action name
        method_name = action_name.replace('-', '_')
        method = getattr(self, method_name)
        return method(**kwargs)
