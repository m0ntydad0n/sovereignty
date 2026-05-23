from sovereignty import redact_model_metadata


def test_redact_model_metadata_removes_secrets_urls_and_private_paths():
    redacted = redact_model_metadata(
        {
            "profile": "local-coder",
            "provider": "openai-compatible",
            "model": "qwen3-coder-local",
            "context_length": 131072,
            "api_key": "sk-secret",
            "base_url": "http://localhost:28080/v1",
            "worker_path": "/Users/monty/local-ai/bin/local-worker",
            "nested": {"token": "gho_secret", "model": "nested-model"},
        }
    )

    assert redacted == {
        "profile": "local-coder",
        "provider": "openai-compatible",
        "model": "qwen3-coder-local",
        "context_length": 131072,
        "nested": {"model": "nested-model"},
    }


def test_redact_model_metadata_drops_token_like_values_even_with_safe_key():
    redacted = redact_model_metadata(
        {
            "model": "qwen3:8b",
            "note": "bearer abcdefghijklmnopqrstuvwxyz1234567890",
            "safe_note": "local extractor lane",
        }
    )

    assert redacted == {"model": "qwen3:8b", "safe_note": "local extractor lane"}
