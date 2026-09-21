import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root directory to path for imports
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.core.exceptions import LLMProviderError
from app.providers.factory import ProviderFactory
from app.schemas.provider import GenerationConfig, LLMRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manual test script for LLM Provider Abstraction Layer."
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="mock",
        choices=["openai", "ollama", "mock"],
        help="Provider to test (default: mock)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model identifier (defaults: gpt-4o-mini for openai, llama3 for ollama)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="Explain quantum computing in two concise bullet points.",
        help="User prompt to send to the LLM",
    )
    parser.add_argument(
        "--system",
        type=str,
        default="You are a helpful AI science communicator.",
        help="Optional system prompt",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)",
    )

    args = parser.parse_args()

    # Determine default model if not provided
    model = args.model
    if not model:
        if args.provider == "openai":
            model = "gpt-4o-mini"
        elif args.provider == "ollama":
            model = "llama3"
        else:
            model = "mock-model-v1"

    print(f"\n==================================================")
    print(f" Testing LLM Provider: {args.provider.upper()}")
    print(f" Target Model:        {model}")
    print(f"==================================================\n")

    provider = ProviderFactory.get_provider(args.provider)

    # Health Check
    print("[1/2] Checking Provider Health...")
    healthy = await provider.health_check()
    print(f"      Health Status: {'HEALTHY (Connected)' if healthy else 'UNHEALTHY / Offline'}\n")

    # Generation Test
    print(f"[2/2] Sending Generation Request...")
    request = LLMRequest(
        model=model,
        user_prompt=args.prompt,
        system_prompt=args.system,
        config=GenerationConfig(temperature=args.temperature),
    )

    try:
        response = await provider.generate(request)

        print("\n---------------- RESPONSE DETAILS ----------------")
        print(f"Provider:       {response.provider_name}")
        print(f"Model:          {response.model}")
        print(f"Latency:        {response.latency_ms} ms")
        print(f"Input Tokens:   {response.input_tokens}")
        print(f"Output Tokens:  {response.output_tokens}")
        print(f"Total Tokens:   {response.total_tokens}")
        print(f"Finish Reason:  {response.finish_reason}")
        print("Metadata:      ", json.dumps(response.metadata, indent=2))
        print("---------------- OUTPUT TEXT ---------------------")
        print(response.text)
        print("--------------------------------------------------\n")

    except LLMProviderError as exc:
        print(f"\n[ERROR] Provider Error caught ({exc.__class__.__name__}): {exc.message}\n")
    except Exception as exc:
        print(f"\n[ERROR] Unexpected Error ({exc.__class__.__name__}): {exc}\n")


if __name__ == "__main__":
    asyncio.run(main())
