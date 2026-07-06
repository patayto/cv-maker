"""Unit tests for the OpenRouter client helper (llm.py)."""

from unittest.mock import Mock, patch

import pytest

import llm


def _response(text):
    return Mock(choices=[Mock(message=Mock(content=text))])


@pytest.mark.unit
def test_models_plural_env_strips_quotes_and_spaces():
    env = {"OPENROUTER_MODELS": '"model/a:free, model/b:free,model/c:free"'}
    with patch.dict('os.environ', env, clear=True):
        assert llm.models() == ["model/a:free", "model/b:free", "model/c:free"]


@pytest.mark.unit
def test_models_singular_fallback_and_default():
    with patch.dict('os.environ', {"OPENROUTER_MODEL": "model/x"}, clear=True):
        assert llm.models() == ["model/x"]
    with patch.dict('os.environ', {}, clear=True):
        assert llm.models() == [llm.DEFAULT_MODEL]


@pytest.mark.unit
def test_complete_falls_through_to_next_model():
    client = Mock()
    client.chat.completions.create.side_effect = [RuntimeError("429"), _response("ok")]
    with patch.dict('os.environ', {"OPENROUTER_MODELS": "m/a,m/b,m/c"}, clear=True), \
         patch.object(llm, "_rotation", iter([0])):
        assert llm.complete(client, "hi") == "ok"

    tried = [call.kwargs["model"] for call in client.chat.completions.create.call_args_list]
    assert tried == ["m/a", "m/b"]


@pytest.mark.unit
def test_complete_round_robin_rotates_start_model():
    client = Mock()
    client.chat.completions.create.return_value = _response("ok")
    with patch.dict('os.environ', {"OPENROUTER_MODELS": "m/a,m/b,m/c"}, clear=True), \
         patch.object(llm, "_rotation", iter([0, 1, 2, 3])):
        for _ in range(4):
            llm.complete(client, "hi")

    tried = [call.kwargs["model"] for call in client.chat.completions.create.call_args_list]
    assert tried == ["m/a", "m/b", "m/c", "m/a"]


@pytest.mark.unit
def test_complete_backs_off_between_cycles_then_raises():
    client = Mock()
    client.chat.completions.create.side_effect = RuntimeError("down")
    with patch.dict('os.environ', {"OPENROUTER_MODELS": "m/a,m/b"}, clear=True), \
         patch.object(llm, "_rotation", iter([0])), \
         patch("llm.time.sleep") as mock_sleep:
        with pytest.raises(RuntimeError, match="All configured OpenRouter models failed"):
            llm.complete(client, "hi")

    # MAX_CYCLES passes over 2 models, sleeping between cycles only
    assert client.chat.completions.create.call_count == llm.MAX_CYCLES * 2
    assert mock_sleep.call_count == llm.MAX_CYCLES - 1
