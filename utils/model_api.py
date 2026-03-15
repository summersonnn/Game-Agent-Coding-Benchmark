"""
Model-agnostic API caller with multi-provider support.
Routes requests to provider-specific endpoints (MiniMax, OpenAI, etc.) when
direct API keys are configured, falling back to OpenRouter for all other models.
Supports model selection by name and detailed reasoning retrieval.
Manages API configuration via environment variables and local files.
"""

import os
from typing import Any, List, Optional
from types import SimpleNamespace
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from dotenv import load_dotenv
from logging_config import setup_logging

logger = setup_logging(__name__)

# Direct provider configuration. When a provider-specific API key is set,
# models from that provider are routed directly instead of through OpenRouter.
DIRECT_PROVIDERS: dict[str, dict[str, Any]] = {
    "minimax": {
        "base_url_env": "MINIMAX_API_BASE_URL",
        "base_url_default": "https://api.minimax.io/v1",
        "api_key_env": "MINIMAX_API_KEY",
        # Map OpenRouter model IDs to direct API model names
        "model_map": {
            "minimax/minimax-m2.5": "MiniMax-M2.5",
            "minimax/minimax-m2.5-highspeed": "MiniMax-M2.5-highspeed",
        },
        "min_temperature": 0.01,  # MiniMax rejects temperature <= 0
    },
}


class ModelAPI:
    """
    A class to handle interactions with LLM APIs using the OpenAI client.
    Supports direct provider routing (MiniMax, OpenAI, etc.) with automatic
    fallback to OpenRouter. Configuration is loaded from environment variables
    and a models.txt file.
    """

    def __init__(self, env_path: Optional[str] = None, models_path: str = "config/models.txt") -> None:
        """
        Initializes the ModelAPI with configuration from environment variables
        and a list of models from a file.

        Args:
            env_path: Optional path to the .env file.
            models_path: Path to the models.txt file.
        """
        # Load environment variables from .env file
        load_dotenv(dotenv_path=env_path)

        # Default (OpenRouter) configuration
        self.base_url = os.getenv("MODEL_API_BASE_URL", "https://openrouter.ai/api/v1")
        self.api_key = os.getenv("MODEL_API_KEY")

        # Load models from file
        self.models: List[str] = []
        self.all_models: List[str] = []
        if os.path.exists(models_path):
            with open(models_path, "r") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        self.all_models.append(stripped)
                        self.models.append(stripped)

        # Common parameters
        try:
            self.max_tokens = int(os.getenv("MODEL_MAX_TOKENS", "8192"))
        except (ValueError, TypeError):
            self.max_tokens = 8192

        try:
            self.temperature = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
        except (ValueError, TypeError):
            self.temperature = 0.7

        # Validate required fields
        if not self.api_key:
            raise ValueError("Missing required environment variable: MODEL_API_KEY")

        # Load token multipliers from file
        self.token_multipliers: dict[str, float] = {}
        max_tokens_path = "config/max_tokens.txt"
        if os.path.exists(max_tokens_path):
            with open(max_tokens_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if ":" in line:
                        key, val = line.split(":", 1)
                        try:
                            self.token_multipliers[key.strip()] = float(val.strip())
                        except ValueError:
                            logger.warning("Invalid multiplier for %s: %s", key, val)

        # Initialize default AsyncOpenAI client (OpenRouter)
        # Clean up base_url if it ends with /api/v (some users might forget the 1)
        if self.base_url.endswith("/api/v"):
            self.base_url += "1"

        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

        # Initialize direct provider clients
        self.provider_clients: dict[str, AsyncOpenAI] = {}
        for provider, cfg in DIRECT_PROVIDERS.items():
            api_key = os.getenv(cfg["api_key_env"])
            if api_key:
                base_url = os.getenv(cfg["base_url_env"], cfg["base_url_default"])
                self.provider_clients[provider] = AsyncOpenAI(
                    base_url=base_url,
                    api_key=api_key,
                )
                logger.info("Direct provider configured: %s → %s", provider, base_url)

    def get_max_tokens(self, game_id: str) -> int:
        """
        Calculates max tokens for a game based on multipliers in config/max_tokens.txt.
        
        Args:
            game_id: The game identifier (e.g., 'A1-Battleship' or 'A1').
            
        Returns:
            The calculated max tokens.
        """
        # Try exact match
        multiplier = self.token_multipliers.get(game_id)
        
        if multiplier is None:
            # Try prefix match (e.g. "A1" from "A1-Battleship")
            prefix = game_id.split("-")[0]
            multiplier = self.token_multipliers.get(prefix)
            
        if multiplier is None:
            # Fallback to DEFAULT
            multiplier = self.token_multipliers.get("DEFAULT", 1.0)
            
        return int(self.max_tokens * multiplier)

    async def call(
        self, 
        prompt: str, 
        model_name: Optional[str] = None,
        reasoning: bool = True, 
        **kwargs: Any
    ) -> Any:
        """
        Sends a completion request to the selected model.
        
        Args:
            prompt: The user prompt.
            model_name: Name of the model from models.txt.
            reasoning: Whether to enable reasoning via extra_body.
            **kwargs: Additional parameters to override defaults.
            
        Returns:
            The ChatCompletion response object from the API.
        """
        if not self.models:
            raise ValueError("No models loaded from models.txt")

        if model_name:
            selected_model = model_name
        else:
            selected_model = self.models[0]


        # Build messages
        messages: List[ChatCompletionMessageParam] = [
            {"role": "user", "content": prompt}
        ]

        # Handle extra_body for reasoning
        extra_body = kwargs.pop("extra_body", {})
        if reasoning:
            if "reasoning" not in extra_body:
                extra_body["reasoning"] = {"effort": "high"}

        # Determine parameters to avoid duplicates in **kwargs
        max_tokens = kwargs.pop("max_tokens", self.max_tokens)
        temperature = kwargs.pop("temperature", self.temperature)

        # We need to ensure stream=False is used
        kwargs["stream"] = False

        try:
            self.timeout = float(os.getenv("MODEL_API_TIMEOUT", "600"))
        except (ValueError, TypeError):
            self.timeout = 600.0

        # Route to direct provider client if available
        client = self.client
        actual_model = selected_model
        provider_prefix = selected_model.split("/")[0]

        if provider_prefix in self.provider_clients:
            client = self.provider_clients[provider_prefix]
            provider_cfg = DIRECT_PROVIDERS[provider_prefix]

            # Map OpenRouter model ID to direct API model name
            base_model = selected_model.split("@")[0]
            actual_model = provider_cfg["model_map"].get(base_model, base_model)

            # Apply provider-specific temperature constraints
            min_temp = provider_cfg.get("min_temperature")
            if min_temp and temperature < min_temp:
                temperature = min_temp

        response = await client.chat.completions.create(
            model=actual_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=self.timeout,
            extra_body=extra_body,
            **kwargs
        )

        # Simplified handling for non-streaming response
        # The response object is directly compatible with what main.py expects
        # We just need to attach our custom 'reasoning_details' attribute to the message
        
        choice = response.choices[0]
        message = choice.message
        
        # Try to extract reasoning if available (provider dependent)
        reasoning_text = None
        if hasattr(message, "reasoning"):
             reasoning_text = message.reasoning
        elif hasattr(message, "reasoning_content"):
             reasoning_text = message.reasoning_content
             
        # Monkey-patch the message object to include reasoning_details
        # Use setattr to avoid type checking issues or read-only errors if it's a Pydantic model
        # But ChatCompletionMessage is usually Pydantic. Safer to just return the response
        # and letting the caller handle it, BUT main.py expects `message.reasoning_details`.
        # Since response objects might be immutable, let's wrap or modify carefully.
        # Actually, main.py expects:
        # response.choices[0].message.content
        # response.choices[0].message.reasoning_details
        
        # Let's create a SimpleNamespace wrapper if needed, or just set the attribute if allowed.
        # OpenRouter/OpenAI Pydantic models might effectively be immutable.
        # Safer approach: Create the mock structure we used before, but populated from the full response.
        
        content = message.content
        usage = response.usage
        
        if not usage:
            usage = SimpleNamespace(completion_tokens=0, cost=0.0)

        mock_message = SimpleNamespace(
            content=content,
            reasoning_details=reasoning_text
        )
        mock_choice = SimpleNamespace(message=mock_message)
        mock_response = SimpleNamespace(
            choices=[mock_choice],
            usage=usage
        )
        
        return mock_response
    @staticmethod
    def resolve_model_interactive(query: str, matches: List[str], context: str = "model") -> str | None:
        """
        Interactively let the user choose between multiple matches.
        
        Args:
            query: The search string that resulted in multiple matches.
            matches: The list of matching strings.
            context: Description for the prompt (e.g., "model", "folder").
            
        Returns:
            The selected match or None if ignored.
        """
        print(f"\nSubstring '{query}' matches multiple {context}s:")
        for i, match in enumerate(matches):
            print(f"  [{i}] {match}")
        
        while True:
            choice = input(f"Select a {context} index (0-{len(matches)-1}) or press Enter to skip: ").strip()
            if not choice:
                return None
            if choice.isdigit():
                idx = int(choice)
                if 0 <= idx < len(matches):
                    return matches[idx]
            print(f"Invalid choice. Please enter a number between 0 and {len(matches)-1}.")



if __name__ == "__main__":
    try:
        api = ModelAPI()
        logger.info("Loaded %d models.", len(api.models))
        for m in api.models:
            logger.info("  - %s", m)
    except Exception as e:
        logger.error("Initialization error: %s", e)
