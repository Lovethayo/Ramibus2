import pytest

from provider_policy import select_provider


def test_defaults_to_local_provider():
    assert select_provider(None) == 'local_gguf'


def test_unknown_provider_fails_closed():
    with pytest.raises(ValueError):
        select_provider('ollama')


def test_remote_provider_requires_opt_in():
    with pytest.raises(ValueError):
        select_provider('openai', allow_remote_apis=False)
