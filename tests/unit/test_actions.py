"""Test charm actions."""

import mock
import imp


def test_get_config_action(wh, monkeypatch):
    """Test get-config action."""
    def mock_get_config():
        return ["mocked", "mocked", "mocked"]

    mock_function = mock.Mock()
    mock_function.side_effect = mock_get_config

    monkeypatch.setattr(wh, "get_config_action", mock_function)
    assert mock_function.call_count == 0
    imp.load_source("get-config", "./actions/get-config")
    assert mock_function.call_count == 1
