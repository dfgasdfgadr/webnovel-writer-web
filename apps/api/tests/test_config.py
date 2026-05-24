import pytest
from app.config import Settings
from app.models.chapter import calculate_word_count


class TestCorsOriginsParsing:
    def test_single_origin(self):
        s = Settings(cors_origins="http://localhost:5173")
        assert s.cors_origin_list == ["http://localhost:5173"]

    def test_comma_separated_origins(self):
        s = Settings(cors_origins="http://localhost:5173,http://localhost:3000")
        assert s.cors_origin_list == ["http://localhost:5173", "http://localhost:3000"]

    def test_comma_with_spaces(self):
        s = Settings(cors_origins=" http://a.com , http://b.com ")
        assert s.cors_origin_list == ["http://a.com", "http://b.com"]

    def test_empty_string(self):
        s = Settings(cors_origins="")
        assert s.cors_origin_list == []

    def test_cors_origins_is_str_type(self):
        s = Settings()
        assert isinstance(s.cors_origins, str)

    def test_extra_fields_ignored(self):
        s = Settings(redis_url="redis://localhost:6379")
        assert hasattr(s, "cors_origins")


class TestConfigDefaults:
    def test_default_database_url(self):
        s = Settings()
        assert "sqlite" in s.database_url

    def test_default_jwt_settings(self):
        s = Settings()
        assert s.jwt_algorithm == "HS256"
        assert s.jwt_expire_hours == 24


class TestCalculateWordCount:
    def test_empty_text(self):
        assert calculate_word_count("") == 0
        assert calculate_word_count(None) == 0

    def test_chinese_characters(self):
        assert calculate_word_count("你好世界") == 4

    def test_mixed_chinese_and_english(self):
        text = "Hello 你好 World"
        count = calculate_word_count(text)
        assert count == 4  # 2 Chinese chars + 2 English words

    def test_punctuation_attached_to_words(self):
        text = "Hello, world! How are you?"
        count = calculate_word_count(text)
        assert count == 5  # "Hello," "world!" "How" "are" "you?"
