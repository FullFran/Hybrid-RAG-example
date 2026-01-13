"""Configuration validation script for MongoDB RAG Agent."""

import sys
from src.settings import load_settings
from src.providers import get_model_info


def mask_credential(value: str) -> str:
    """Mask credentials for safe display."""
    if not value or len(value) < 8:
        return "***"
    return value[:4] + "..." + value[-4:]


def validate_config() -> bool:
    """
    Validate configuration and display settings.

    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        print("=" * 60)
        print("MongoDB RAG Agent - Configuration Validation")
        print("=" * 60)
        print()

        # Load settings
        print("[1/4] Loading settings...")
        settings = load_settings()
        print("[OK] Settings loaded successfully")
        print()

        # Validate MongoDB configuration
        print("[2/4] Validating MongoDB configuration...")
        print(f"  MongoDB URI: {mask_credential(settings.mongodb_uri)}")
        print(f"  Database: {settings.mongodb_database}")
        print(f"  Documents Collection: {settings.mongodb_collection_documents}")
        print(f"  Chunks Collection: {settings.mongodb_collection_chunks}")
        print(f"  Vector Index: {settings.mongodb_vector_index}")
        print(f"  Text Index: {settings.mongodb_text_index}")
        print("[OK] MongoDB configuration present")
        print()

        # Validate LLM configuration
        print("[3/4] Validating LLM configuration...")
        model_info = get_model_info()
        print(f"  Provider: {model_info['llm_provider']}")
        print(f"  Model: {model_info['llm_model']}")
        print(f"  Base URL: {model_info['llm_base_url']}")
        print(f"  API Key: {mask_credential(settings.llm_api_key)}")
        print("[OK] LLM configuration present")
        print()

        # Validate Embedding configuration
        print("[4/4] Validating Embedding configuration...")
        print(f"  Provider: {settings.embedding_provider}")
        print(f"  Model: {settings.embedding_model}")
        print(f"  Dimension: {settings.embedding_dimension}")
        print(f"  API Key: {mask_credential(settings.embedding_api_key)}")
        print("[OK] Embedding configuration present")
        print()

        # Success summary
        print("=" * 60)
        print("[OK] ALL CONFIGURATION CHECKS PASSED")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Add documents to the ./documents/ folder")
        print("2. Run ingestion: uv run python -m src.ingestion.ingest -d ./documents")
        print("3. Create search indexes in MongoDB Atlas (after ingestion completes)")
        print("   See README.md for index creation instructions")
        print()

        return True

    except ValueError as e:
        print()
        print("=" * 60)
        print("[FAIL] CONFIGURATION VALIDATION FAILED")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        print()
        print("Please check your .env file and ensure all required variables are set.")
        print("See .env.example for required variables.")
        print()
        return False

    except Exception as e:
        print()
        print("=" * 60)
        print("[FAIL] UNEXPECTED ERROR")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        print()
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)
