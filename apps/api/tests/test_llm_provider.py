"""Tests for LLMProvider priority logic: user settings > .env > defaults."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.llm import LLMProvider, LLMMessage, LLMResponse


class TestLLMProviderConstructor:
    def test_defaults_from_env(self):
        with patch("app.agents.llm.settings") as mock_settings:
            mock_settings.llm_base_url = "https://api.openai.com/v1"
            mock_settings.llm_api_key = "sk-env-key"
            mock_settings.llm_model = "gpt-4o"

            provider = LLMProvider()
            assert provider.base_url == "https://api.openai.com/v1"
            assert provider.api_key == "sk-env-key"
            assert provider.model == "gpt-4o"

    def test_constructor_params_override_env(self):
        with patch("app.agents.llm.settings") as mock_settings:
            mock_settings.llm_base_url = "https://api.openai.com/v1"
            mock_settings.llm_api_key = "sk-env-key"
            mock_settings.llm_model = "gpt-4o"

            provider = LLMProvider(
                base_url="https://custom.api.com/v1",
                api_key="sk-custom-key",
                model="custom-model",
            )
            assert provider.base_url == "https://custom.api.com/v1"
            assert provider.api_key == "sk-custom-key"
            assert provider.model == "custom-model"

    def test_constructor_partial_override(self):
        with patch("app.agents.llm.settings") as mock_settings:
            mock_settings.llm_base_url = "https://api.openai.com/v1"
            mock_settings.llm_api_key = ""
            mock_settings.llm_model = "gpt-4o"

            provider = LLMProvider(api_key="sk-override-key")
            assert provider.base_url == "https://api.openai.com/v1"
            assert provider.api_key == "sk-override-key"
            assert provider.model == "gpt-4o"


class TestLLMProviderForUser:
    @pytest.mark.asyncio
    async def test_for_user_without_db_uses_env_defaults(self):
        with patch("app.agents.llm.settings") as mock_settings:
            mock_settings.llm_base_url = "https://api.openai.com/v1"
            mock_settings.llm_api_key = "sk-env-key"
            mock_settings.llm_model = "gpt-4o"

            provider = await LLMProvider.for_user("user-1", db_session=None)
            assert provider.api_key == "sk-env-key"
            assert provider.base_url == "https://api.openai.com/v1"
            assert provider.model == "gpt-4o"
            assert provider.user_id == "user-1"

    @pytest.mark.asyncio
    async def test_for_user_with_db_mock_applies_user_settings(self):
        # Mock the DB session and query result
        mock_session = AsyncMock()
        mock_record = MagicMock()
        mock_record.api_key_encrypted = None
        mock_record.base_url = "https://user-api.example.com/v1"
        mock_record.model = "user-gpt-4o"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_record
        mock_session.execute.return_value = mock_result

        # Need to patch _decrypt_api_key since record has no encrypted key
        provider = await LLMProvider.for_user("user-1", db_session=mock_session)
        assert provider.base_url == "https://user-api.example.com/v1"
        assert provider.model == "user-gpt-4o"
        assert provider.user_id == "user-1"

    @pytest.mark.asyncio
    async def test_for_user_with_encrypted_key(self):
        """When user has encrypted API key, it should be decrypted and used."""
        from app.routers.settings import _encrypt_api_key

        encrypted = _encrypt_api_key("sk-user-encrypted-key")

        mock_session = AsyncMock()
        mock_record = MagicMock()
        mock_record.api_key_encrypted = encrypted
        mock_record.base_url = "https://user-api.com/v1"
        mock_record.model = "user-model"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_record
        mock_session.execute.return_value = mock_result

        provider = await LLMProvider.for_user("user-1", db_session=mock_session)
        assert provider.api_key == "sk-user-encrypted-key"
        assert provider.base_url == "https://user-api.com/v1"
        assert provider.model == "user-model"

    @pytest.mark.asyncio
    async def test_for_user_no_record_falls_back_to_env(self):
        with patch("app.agents.llm.settings") as mock_settings:
            mock_settings.llm_base_url = "https://api.openai.com/v1"
            mock_settings.llm_api_key = "sk-env-key"
            mock_settings.llm_model = "gpt-4o"

            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result

            provider = await LLMProvider.for_user("user-1", db_session=mock_session)
            assert provider.api_key == "sk-env-key"
            assert provider.base_url == "https://api.openai.com/v1"
            assert provider.model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_for_user_db_error_graceful_fallback(self):
        """If DB query fails, should still return a working provider with env defaults."""
        with patch("app.agents.llm.settings") as mock_settings:
            mock_settings.llm_base_url = "https://api.openai.com/v1"
            mock_settings.llm_api_key = "sk-env-key"
            mock_settings.llm_model = "gpt-4o"

            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("DB connection failed")

            provider = await LLMProvider.for_user("user-1", db_session=mock_session)
            assert provider.api_key == "sk-env-key"
            assert provider.base_url == "https://api.openai.com/v1"
            assert provider.model == "gpt-4o"


class TestLLMProviderMessages:
    def test_llm_message_creation(self):
        msg = LLMMessage(role="system", content="You are a helpful assistant.")
        assert msg.role == "system"
        assert msg.content == "You are a helpful assistant."

    def test_llm_response_creation(self):
        resp = LLMResponse(content="Hello", token_input=10, token_output=5)
        assert resp.content == "Hello"
        assert resp.token_input == 10
        assert resp.token_output == 5


class TestLLMProviderChat:
    @pytest.mark.asyncio
    async def test_chat_calls_openai_endpoint(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello from LLM"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 4},
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response), \
             patch("app.agents.llm.settings") as mock_settings:
            mock_settings.llm_base_url = "https://api.test.com/v1"
            mock_settings.llm_api_key = "sk-test"
            mock_settings.llm_model = "gpt-4o"

            provider = LLMProvider()
            messages = [LLMMessage(role="user", content="Hi")]
            resp = await provider.chat(messages)

            assert resp.content == "Hello from LLM"
            assert resp.token_input == 3
            assert resp.token_output == 4

    @pytest.mark.asyncio
    async def test_chat_with_user_settings_overrides_env(self):
        """chat() uses user settings when provider was created with for_user."""
        from app.routers.settings import _encrypt_api_key

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "User-specific response"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 2},
        }

        encrypted = _encrypt_api_key("sk-user-key")

        mock_session = AsyncMock()
        mock_record = MagicMock()
        mock_record.api_key_encrypted = encrypted
        mock_record.base_url = "https://user-api.com/v1"
        mock_record.model = "user-model"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_record
        mock_session.execute.return_value = mock_result

        provider = await LLMProvider.for_user("user-1", db_session=mock_session)

        # Verify user settings are applied
        assert provider.api_key == "sk-user-key"
        assert provider.base_url == "https://user-api.com/v1"
        assert provider.model == "user-model"

        # Now chat should use these user settings
        with patch("httpx.AsyncClient.post", return_value=mock_response):
            messages = [LLMMessage(role="user", content="Hi")]
            resp = await provider.chat(messages)
            assert resp.content == "User-specific response"
