from unittest.mock import MagicMock, mock_open, patch

import pytest

# Adjust import path if necessary
from proxies.get_proxies import load_proxies

# from paths import CLEANED_PROXIES_DIR # No longer needed for direct verification here

# --- Tests for load_proxies ---


@patch("proxies.get_proxies.CLEANED_PROXIES_DIR")
def test_load_proxies_file_exists_and_has_content(MockCleanedProxiesDir):
    # Test loading proxies when the file exists and has content.
    protocol = "http"
    mock_file_content = "proxy1:port1\nproxy2:port2\n proxy3:port3 \n"  # Includes whitespace
    expected_proxies = ["proxy1:port1", "proxy2:port2", "proxy3:port3"]

    # Configure the mock for CLEANED_PROXIES_DIR / f"{protocol}.txt"
    mock_final_path = MagicMock()
    mock_final_path.exists = MagicMock(return_value=True)
    MockCleanedProxiesDir.__truediv__ = MagicMock(return_value=mock_final_path)

    # Mock open() for reading the file
    m_open = mock_open(read_data=mock_file_content)
    with patch("builtins.open", m_open):
        proxies = load_proxies(protocol)

    # Assert that CLEANED_PROXIES_DIR / f"{protocol}.txt" was called
    MockCleanedProxiesDir.__truediv__.assert_called_once_with(f"{protocol}.txt")

    # Assert that open was called with the correct path from the mocked Path object
    m_open.assert_called_once_with(mock_final_path, "r", encoding="utf-8")
    assert proxies == expected_proxies


@patch("proxies.get_proxies.CLEANED_PROXIES_DIR")
def test_load_proxies_file_exists_but_empty(MockCleanedProxiesDir):
    # Test loading proxies when the file exists but is empty.
    protocol = "https"
    mock_file_content = ""
    expected_proxies = []

    mock_final_path = MagicMock()
    mock_final_path.exists = MagicMock(return_value=True)
    MockCleanedProxiesDir.__truediv__ = MagicMock(return_value=mock_final_path)

    m_open = mock_open(read_data=mock_file_content)
    with patch("builtins.open", m_open):
        proxies = load_proxies(protocol)

    MockCleanedProxiesDir.__truediv__.assert_called_once_with(f"{protocol}.txt")
    m_open.assert_called_once_with(mock_final_path, "r", encoding="utf-8")
    assert proxies == expected_proxies


@patch("proxies.get_proxies.CLEANED_PROXIES_DIR")
def test_load_proxies_file_exists_with_only_whitespace_lines(MockCleanedProxiesDir):
    # Test loading proxies when the file exists but only has whitespace lines.
    protocol = "socks5"
    mock_file_content = "\n   \n\t\n"  # Only whitespace lines
    expected_proxies = []

    mock_final_path = MagicMock()
    mock_final_path.exists = MagicMock(return_value=True)
    MockCleanedProxiesDir.__truediv__ = MagicMock(return_value=mock_final_path)

    m_open = mock_open(read_data=mock_file_content)
    with patch("builtins.open", m_open):
        proxies = load_proxies(protocol)

    MockCleanedProxiesDir.__truediv__.assert_called_once_with(f"{protocol}.txt")
    m_open.assert_called_once_with(mock_final_path, "r", encoding="utf-8")
    assert proxies == expected_proxies


@patch("proxies.get_proxies.CLEANED_PROXIES_DIR")
def test_load_proxies_file_not_exist(MockCleanedProxiesDir):
    # Test loading proxies when the file does not exist.
    protocol = "socks4"
    expected_proxies = []

    mock_final_path = MagicMock()
    mock_final_path.exists = MagicMock(return_value=False)  # File does not exist
    MockCleanedProxiesDir.__truediv__ = MagicMock(return_value=mock_final_path)

    m_open = mock_open()  # mock_open just in case, though it shouldn't be called
    with patch("builtins.open", m_open):
        proxies = load_proxies(protocol)

    MockCleanedProxiesDir.__truediv__.assert_called_once_with(f"{protocol}.txt")
    m_open.assert_not_called()  # open should not be called if file.exists() is False
    assert proxies == expected_proxies


@patch("proxies.get_proxies.CLEANED_PROXIES_DIR")
def test_load_proxies_different_protocols_map_to_different_files(MockCleanedProxiesDir):
    # Test that different protocols result in different file paths being checked.
    protocols_to_test = ["http", "https", "socks5", "socks4"]

    for protocol in protocols_to_test:
        MockCleanedProxiesDir.reset_mock()  # Reset the main mock for CLEANED_PROXIES_DIR

        mock_final_path_for_protocol = MagicMock()
        mock_final_path_for_protocol.exists = MagicMock(return_value=False)  # Assume files don't exist

        # Ensure that when CLEANED_PROXIES_DIR / "protocol.txt" is called, it returns our specific mock
        MockCleanedProxiesDir.__truediv__ = MagicMock(return_value=mock_final_path_for_protocol)

        load_proxies(protocol)

        MockCleanedProxiesDir.__truediv__.assert_called_once_with(f"{protocol}.txt")
