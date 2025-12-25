import logging  # Added for caplog.set_level
import subprocess
from pathlib import Path
from unittest.mock import ANY, MagicMock, call, mock_open, patch

import pytest
import requests  # For requests.exceptions.RequestException

# Adjust import path as necessary, assuming 'proxies' is a package
from proxies.get_free_proxies import (  # Constants needed for mocking paths if not patching Path directly at class level
    PROXY_PROTOCOLS,
    RAW_PROXIES_DIR,
    download_github_file,
    download_proxies,
    include_scraped_proxies,
    parse_github_url,
    run_proxy_scraper_all_protocols,
)

# --- Tests for parse_github_url ---


def test_parse_github_url_valid():
    url = "https://github.com/owner/repo/blob/main/path/to/file.txt"
    repo, file_path = parse_github_url(url)
    assert repo == "owner/repo"
    assert file_path == "main/path/to/file.txt"  # Updated expected path


def test_parse_github_url_valid_with_branch_in_path():
    # This regex might not handle branches in path correctly if not careful,
    # but current regex is `blob/[^/]+/(.+)` so it should capture after branch.
    url = "https://github.com/owner/repo/blob/feature/new-stuff/file.txt"
    repo, file_path = parse_github_url(url)
    assert repo == "owner/repo"
    assert file_path == "feature/new-stuff/file.txt"


def test_parse_github_url_invalid_format():
    url = "https://example.com/owner/repo/blob/main/file.txt"
    with pytest.raises(ValueError) as excinfo:
        parse_github_url(url)
    assert "Invalid GitHub file URL format" in str(excinfo.value)


def test_parse_github_url_not_a_file_url():
    url = "https://github.com/owner/repo/"
    with pytest.raises(ValueError) as excinfo:
        parse_github_url(url)
    assert "Invalid GitHub file URL format" in str(excinfo.value)


# --- Tests for download_github_file ---


@patch("proxies.get_free_proxies.requests.get")
@patch("proxies.get_free_proxies.os.getenv")  # To mock GITHUB_TOKEN
def test_download_github_file_success(mock_getenv, mock_requests_get):
    mock_getenv.return_value = "test_token"  # Simulate GITHUB_TOKEN is set
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Simulate the structure of the GitHub API response for file content
    mock_response.json.return_value = {
        "content": "cHJveHkxCnByb3h5Mg==",
        "encoding": "base64",
    }  # "proxy1\nproxy2" base64 encoded
    mock_requests_get.return_value = mock_response

    # Patch HEADERS directly if it's a global in the module, or ensure getenv is used by HEADERS construction
    # For this test, assuming HEADERS in get_free_proxies uses os.getenv("GITHUB_TOKEN")

    content = download_github_file("owner/repo", "path/file.txt")

    expected_api_url = "https://api.github.com/repos/owner/repo/contents/path/file.txt"
    # HEADERS should be constructed with the token from mock_getenv
    expected_headers = {"Accept": "application/vnd.github.v3.raw", "Authorization": "token test_token"}
    mock_requests_get.assert_called_once_with(expected_api_url, headers=expected_headers)
    assert content == "proxy1\nproxy2"


@patch("proxies.get_free_proxies.requests.get")
@patch("proxies.get_free_proxies.os.getenv")
def test_download_github_file_failure(mock_getenv, mock_requests_get):
    mock_getenv.return_value = None  # No GITHUB_TOKEN
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.text = "Not Found Details"  # GitHub often returns JSON for errors too
    mock_response.json.return_value = {"message": "Not Found Details"}  # Simulate JSON error response
    mock_requests_get.return_value = mock_response

    with pytest.raises(Exception) as excinfo:
        download_github_file("owner/repo", "path/file.txt")

    # Check the error message construction
    # Original code uses response.text, but GitHub API usually returns JSON error messages.
    # If the code uses response.json()['message'] for errors, the expected string would change.
    # Assuming it uses response.text for now.
    assert "Failed to fetch path/file.txt from owner/repo: 404 Not Found Details" in str(excinfo.value)


# --- Tests for run_proxy_scraper_all_protocols ---


@patch("proxies.get_free_proxies.subprocess.run")
@patch("proxies.get_free_proxies.RAW_PROXIES_DIR")  # Patch the actual Path object
def test_run_proxy_scraper_all_protocols_success(MockRawProxiesDir, mock_subprocess_run):

    created_mock_paths = {}

    def truediv_side_effect(filename):
        mock_path = MagicMock(spec=Path, name=f"Path_{filename}")
        # Ensure __str__ returns something usable by subprocess.run
        mock_path.__str__ = MagicMock(return_value=f"/mocked_path/{filename}")
        created_mock_paths[filename] = mock_path
        return mock_path

    MockRawProxiesDir.__truediv__ = MagicMock(side_effect=truediv_side_effect)

    protocols_to_run = ["http", "socks5"]

    result_files = run_proxy_scraper_all_protocols(protocols_to_run)

    # Define expected_files AFTER run_proxy_scraper_all_protocols has populated created_mock_paths
    expected_files = [created_mock_paths["iw4p_scraped_http.txt"], created_mock_paths["iw4p_scraped_socks5.txt"]]

    assert mock_subprocess_run.call_count == len(protocols_to_run)
    # Adjust assert_any_call to remove capture_output and text
    mock_subprocess_run.assert_any_call(
        ["proxy_scraper", "-p", "http", "-o", str(created_mock_paths["iw4p_scraped_http.txt"])], check=True
    )
    mock_subprocess_run.assert_any_call(
        ["proxy_scraper", "-p", "socks5", "-o", str(created_mock_paths["iw4p_scraped_socks5.txt"])], check=True
    )
    assert result_files == expected_files


@patch("proxies.get_free_proxies.subprocess.run")
@patch("proxies.get_free_proxies.RAW_PROXIES_DIR")  # Patch the actual Path object
def test_run_proxy_scraper_all_protocols_some_fail(MockRawProxiesDir, mock_subprocess_run):
    created_mock_paths = {}

    def truediv_side_effect(filename):
        mock_path = MagicMock(spec=Path, name=f"Path_{filename}")
        mock_path.__str__ = MagicMock(return_value=f"/mocked_path/{filename}")
        created_mock_paths[filename] = mock_path
        return mock_path

    MockRawProxiesDir.__truediv__ = MagicMock(side_effect=truediv_side_effect)

    # Simulate failure for 'http', success for 'https'
    def subprocess_side_effect(*args, **kwargs):
        if args[0][2] == "http":  # Check protocol arg
            raise subprocess.CalledProcessError(1, args[0], stderr="cmd failed error output")
        # Successful run
        completed_process_mock = MagicMock(spec=subprocess.CompletedProcess)
        completed_process_mock.stdout = "Success output"
        completed_process_mock.stderr = ""
        completed_process_mock.returncode = 0
        return completed_process_mock

    mock_subprocess_run.side_effect = subprocess_side_effect

    protocols_to_run = ["http", "https"]
    result_files = run_proxy_scraper_all_protocols(protocols_to_run)

    # Define expected_files AFTER run_proxy_scraper_all_protocols has populated created_mock_paths
    # Only https should be in the result
    expected_files = [created_mock_paths["iw4p_scraped_https.txt"]]

    assert mock_subprocess_run.call_count == len(protocols_to_run)
    assert result_files == expected_files


# --- Tests for include_scraped_proxies ---


@patch("builtins.open", new_callable=mock_open, read_data="proxy_a:1\nproxy_b:2")
@patch("proxies.get_free_proxies.Path")  # Mock Path to control file existence
def test_include_scraped_proxies_file_exists(MockPath, mock_file_open_builtin):
    # This Path mock is for the Path object created *inside* include_scraped_proxies
    # It's not for the mock_scraped_file_path argument itself.
    # The argument mock_scraped_file_path should behave like a Path.
    mock_scraped_file_path_arg = MagicMock(spec=Path)
    mock_scraped_file_path_arg.exists = MagicMock(return_value=True)
    # MockPath is not strictly needed here if mock_scraped_file_path_arg is well-defined
    # and the function doesn't create new Path objects internally from strings.
    # Let's assume mock_scraped_file_path_arg is what's checked for exists() and opened.

    seen_proxies = {"proxy_c:3"}
    mock_outfile_handle = MagicMock()  # Mock the output file handle (e.g., from another mock_open)
    mock_outfile_handle.write = MagicMock()

    include_scraped_proxies(mock_scraped_file_path_arg, seen_proxies, mock_outfile_handle)

    # Ensure open was called on the mock_scraped_file_path_arg
    mock_file_open_builtin.assert_called_once_with(mock_scraped_file_path_arg, "r", encoding="utf-8")

    # Check calls to outfile.write
    expected_calls = [call("proxy_a:1\n"), call("proxy_b:2\n")]
    mock_outfile_handle.write.assert_has_calls(expected_calls, any_order=False)
    assert "proxy_a:1" in seen_proxies
    assert "proxy_b:2" in seen_proxies


@patch("proxies.get_free_proxies.Path")  # Mock Path to control file existence
def test_include_scraped_proxies_file_not_exist(MockPath):
    mock_scraped_file_path_arg = MagicMock(spec=Path)
    mock_scraped_file_path_arg.exists = MagicMock(return_value=False)  # File does not exist

    seen_proxies = set()
    mock_outfile_handle = MagicMock()
    mock_outfile_handle.write = MagicMock()  # Should not be called

    # builtins.open should not be called if the file doesn't exist.
    with patch("builtins.open", mock_open()) as m_open:
        include_scraped_proxies(mock_scraped_file_path_arg, seen_proxies, mock_outfile_handle)
        m_open.assert_not_called()

    mock_outfile_handle.write.assert_not_called()


# (Assuming previous imports like pytest, patch, MagicMock, Path, etc. are already in the file)
from proxies.get_free_proxies import PROXY_VALID_THRESHOLD  # For testing ensure_valid_pools
from proxies.get_free_proxies import (  # PROXY_PROTOCOLS,      # Already imported at the top
    ensure_valid_pools,
    refresh_free_proxies,
)

# --- Tests for refresh_free_proxies ---


@patch("proxies.get_free_proxies.download_proxies")
@patch("proxies.get_free_proxies.run_proxy_checker")
@patch("proxies.get_free_proxies.organize_checked_proxies")
def test_refresh_free_proxies_orchestration(mock_organize_checked, mock_run_checker, mock_download_proxies):
    # Test the orchestration of download, check, and organize.
    mock_raw_path = MagicMock(spec=Path, name="mock_raw_download_path")
    mock_download_proxies.return_value = mock_raw_path

    # Need to import these from the module under test to check against them
    from proxies.get_free_proxies import GITHUB_FILE_URLS, STATIC_URLS

    refresh_free_proxies()

    mock_download_proxies.assert_called_once_with(STATIC_URLS, GITHUB_FILE_URLS)
    mock_run_checker.assert_called_once_with(mock_raw_path)
    mock_organize_checked.assert_called_once_with()


# --- Tests for ensure_valid_pools ---


@patch("proxies.get_free_proxies.count_valid_proxies")  # Mocks the one in get_free_proxies.py
@patch("proxies.get_free_proxies.refresh_free_proxies")
def test_ensure_valid_pools_all_pools_valid(mock_refresh_proxies, mock_count_valid):
    # Test scenario where all proxy pools have sufficient proxies.
    # Make count_valid_proxies return a count above the threshold for all protocols.
    mock_count_valid.return_value = PROXY_VALID_THRESHOLD + 5

    ensure_valid_pools()

    assert mock_count_valid.call_count == len(PROXY_PROTOCOLS)
    for protocol in PROXY_PROTOCOLS:
        mock_count_valid.assert_any_call(protocol)

    mock_refresh_proxies.assert_not_called()  # refresh_free_proxies should not be called


@patch("proxies.get_free_proxies.count_valid_proxies")
@patch("proxies.get_free_proxies.refresh_free_proxies")
def test_ensure_valid_pools_one_pool_invalid(mock_refresh_proxies, mock_count_valid, caplog):
    # Test scenario where one proxy pool is below the threshold.

    # Make count_valid_proxies return valid for first, then invalid, then valid
    # to ensure the loop breaks after the first invalid and refresh is called.
    def count_side_effect(protocol):
        if protocol == PROXY_PROTOCOLS[0]:  # e.g., "http"
            return PROXY_VALID_THRESHOLD + 5
        if protocol == PROXY_PROTOCOLS[1]:  # e.g., "https"
            return PROXY_VALID_THRESHOLD - 1  # Invalid
        return PROXY_VALID_THRESHOLD + 5  # Others valid

    mock_count_valid.side_effect = count_side_effect

    ensure_valid_pools()

    # count_valid_proxies should be called for the first two protocols only due to break
    assert mock_count_valid.call_count == 2
    mock_count_valid.assert_any_call(PROXY_PROTOCOLS[0])
    mock_count_valid.assert_any_call(PROXY_PROTOCOLS[1])

    mock_refresh_proxies.assert_called_once()  # refresh_free_proxies should be called
    assert f"Not enough valid proxies for {PROXY_PROTOCOLS[1]}" in caplog.text


@patch("proxies.get_free_proxies.count_valid_proxies")
@patch("proxies.get_free_proxies.refresh_free_proxies")
def test_ensure_valid_pools_all_pools_initially_invalid(mock_refresh_proxies, mock_count_valid, caplog):
    # Test scenario where the first checked pool is invalid.
    mock_count_valid.return_value = PROXY_VALID_THRESHOLD - 1  # All are invalid, but loop breaks on first.

    ensure_valid_pools()

    # count_valid_proxies should be called only for the first protocol
    mock_count_valid.assert_called_once_with(PROXY_PROTOCOLS[0])

    mock_refresh_proxies.assert_called_once()
    assert f"Not enough valid proxies for {PROXY_PROTOCOLS[0]}" in caplog.text


# (Assuming previous imports like pytest, patch, MagicMock, Path, etc. are already in the file)
# Add os if not already there for os.chdir mocking
import os

from proxies.get_free_proxies import CLEANED_PROXIES_DIR  # Imported for verifying output paths
from proxies.get_free_proxies import PROXY_CHECKER_PATH  # Imported for verifying os.chdir
from proxies.get_free_proxies import (
    organize_checked_proxies,
    run_proxy_checker,
)

# --- Tests for run_proxy_checker ---


@patch("proxies.get_free_proxies.os.chdir")
@patch("proxies.get_free_proxies.subprocess.run")
def test_run_proxy_checker_success(mock_subprocess_run, mock_os_chdir):
    # Test successful execution of the proxy checker script.
    mock_input_path = MagicMock(spec=Path)

    # Mock the CompletedProcess object that subprocess.run returns on success
    completed_process_mock = MagicMock(spec=subprocess.CompletedProcess)
    completed_process_mock.stdout = "Checker output"
    completed_process_mock.stderr = ""
    completed_process_mock.returncode = 0
    mock_subprocess_run.return_value = completed_process_mock

    run_proxy_checker(mock_input_path)  # input_path is not used by current run_proxy_checker

    mock_os_chdir.assert_called_once_with(PROXY_CHECKER_PATH)
    # The input_path IS passed to subprocess.run in the source code.
    mock_subprocess_run.assert_called_once_with(
        ["./target/release/proxy-scraper-checker", str(mock_input_path)], check=True, capture_output=True, text=True
    )


@patch("proxies.get_free_proxies.os.chdir")
@patch("proxies.get_free_proxies.subprocess.run")
def test_run_proxy_checker_failure(mock_subprocess_run, mock_os_chdir, caplog):
    # Test handling of failure when the proxy checker script fails.
    mock_input_path = MagicMock(spec=Path)
    # Simulate CalledProcessError
    # The error object needs specific attributes: cmd, returncode, and optionally output/stderr
    # Ensure the cmd in the error matches the expected call
    cmd_that_failed = ["./target/release/proxy-scraper-checker", str(mock_input_path)]
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=cmd_that_failed, stderr="Error output from checker"
    )

    run_proxy_checker(mock_input_path)

    mock_os_chdir.assert_called_once_with(PROXY_CHECKER_PATH)
    mock_subprocess_run.assert_called_once_with(cmd_that_failed, check=True, capture_output=True, text=True)
    # Check that an error was logged
    assert "proxy-scraper-checker failed" in caplog.text
    assert "Error output from checker" in caplog.text  # Check if stderr is logged


# --- Tests for organize_checked_proxies ---


# Patching PROXY_CHECKER_PATH and CLEANED_PROXIES_DIR at the module level
@patch("proxies.get_free_proxies.PROXY_CHECKER_PATH")  # Let patch create default MagicMock
@patch("proxies.get_free_proxies.CLEANED_PROXIES_DIR")  # Let patch create default MagicMock
@patch("builtins.open", new_callable=mock_open)  # Mocks open for file reading/writing
def test_organize_checked_proxies_success(mock_open_builtin, mock_CLEANED_PROXIES_DIR, mock_PROXY_CHECKER_PATH, caplog):
    # Note: The patched arguments are now mock_CLEANED_PROXIES_DIR and mock_PROXY_CHECKER_PATH
    caplog.set_level(logging.INFO)  # Ensure INFO logs are captured
    # Test successful organization of checked proxies.

    # --- Setup mock Path objects ---
    # Mock for PROXY_CHECKER_PATH / "out/proxies"
    mock_checker_out_proxies_dir = MagicMock(spec=Path)
    mock_checker_out_proxies_dir.exists.return_value = True
    # mock_PROXY_CHECKER_PATH is a MagicMock. Its attributes like __truediv__ are also MagicMocks by default.
    # We need to set the side_effect of this child mock.
    mock_PROXY_CHECKER_PATH.__truediv__.side_effect = lambda x: (
        mock_checker_out_proxies_dir if x == "out/proxies" else MagicMock(spec=Path)
    )
    # simplified: PROXY_CHECKER_PATH / "out/proxies"

    # Mock files found by glob
    mock_http_txt_from_checker = MagicMock(spec=Path)
    mock_http_txt_from_checker.name = "http.txt"

    mock_https_txt_from_checker = MagicMock(spec=Path)
    mock_https_txt_from_checker.name = "https.txt"
    mock_checker_out_proxies_dir.glob.return_value = [mock_http_txt_from_checker, mock_https_txt_from_checker]

    # Mock target paths in CLEANED_PROXIES_DIR
    mock_target_http_txt = MagicMock(spec=Path)
    mock_target_http_txt.name = "http.txt"  # Configure .name for logging
    mock_target_https_txt = MagicMock(spec=Path)
    mock_target_https_txt.name = "https.txt"  # Configure .name for logging

    def cleaned_dir_truediv_side_effect(filename):
        if filename == "http.txt":
            return mock_target_http_txt
        elif filename == "https.txt":
            return mock_target_https_txt
        return MagicMock(spec=Path)  # Should not happen in this test

    # Correctly indented and assigned after the function definition
    mock_CLEANED_PROXIES_DIR.__truediv__.side_effect = cleaned_dir_truediv_side_effect

    # Mock file contents for reading
    http_proxies_content = "1.1.1.1:80\n2.2.2.2:80\n1.1.1.1:80"  # Duplicates, unsorted
    https_proxies_content = "3.3.3.3:443\n4.4.4.4:443"

    # Mock file handles for writing (to capture written content)
    mock_http_write_handle = mock_open().return_value  # Use different instances for different files
    mock_https_write_handle = mock_open().return_value

    def open_side_effect(path_obj, mode, encoding=None):  # Added encoding
        if path_obj == mock_http_txt_from_checker and mode == "r":
            return mock_open(read_data=http_proxies_content).return_value
        if path_obj == mock_https_txt_from_checker and mode == "r":
            return mock_open(read_data=https_proxies_content).return_value
        if path_obj == mock_target_http_txt and mode == "w":
            return mock_http_write_handle
        if path_obj == mock_target_https_txt and mode == "w":
            return mock_https_write_handle
        # Fallback for any other unexpected open calls
        raise FileNotFoundError(f"Test mock_open: Unexpected open call: {path_obj}, mode {mode}")

    mock_open_builtin.side_effect = open_side_effect

    organize_checked_proxies()

    # --- Assertions ---
    mock_PROXY_CHECKER_PATH.__truediv__.assert_called_once_with("out/proxies")
    mock_checker_out_proxies_dir.exists.assert_called_once()
    mock_checker_out_proxies_dir.glob.assert_called_once_with("*.txt")

    # Check open calls for reading (order might vary based on glob)
    mock_open_builtin.assert_any_call(mock_http_txt_from_checker, "r", encoding="utf-8")
    mock_open_builtin.assert_any_call(mock_https_txt_from_checker, "r", encoding="utf-8")

    # Check open calls for writing
    mock_open_builtin.assert_any_call(mock_target_http_txt, "w", encoding="utf-8")
    mock_open_builtin.assert_any_call(mock_target_https_txt, "w", encoding="utf-8")

    # Assert correct, sorted, unique content was written
    expected_http_writes = [call("1.1.1.1:80\n"), call("2.2.2.2:80\n")]  # Sorted, unique
    mock_http_write_handle.write.assert_has_calls(expected_http_writes)

    expected_https_writes = [call("3.3.3.3:443\n"), call("4.4.4.4:443\n")]  # Already sorted, unique
    mock_https_write_handle.write.assert_has_calls(expected_https_writes)

    assert f"Cleaned 2 proxies into {mock_http_txt_from_checker.name}" in caplog.text
    assert f"Cleaned 2 proxies into {mock_https_txt_from_checker.name}" in caplog.text


@patch("proxies.get_free_proxies.PROXY_CHECKER_PATH", new_callable=MagicMock)
def test_organize_checked_proxies_output_dir_not_exist(mock_checker_path_global, caplog):
    # Test scenario where the checker's output directory does not exist.

    mock_output_dir_obj = MagicMock(spec=Path)
    mock_output_dir_obj.exists.return_value = False  # Does not exist
    mock_checker_path_global.__truediv__.return_value = mock_output_dir_obj  # for PROXY_CHECKER_PATH / "out/proxies"

    # Mock open to ensure it's not called for file operations if dir doesn't exist
    with patch("builtins.open", mock_open()) as m_open:
        organize_checked_proxies()
        m_open.assert_not_called()

    mock_checker_path_global.__truediv__.assert_called_once_with("out/proxies")
    mock_output_dir_obj.exists.assert_called_once()
    mock_output_dir_obj.glob.assert_not_called()  # Should not glob if dir doesn't exist
    assert "Output directory from proxy-scraper-checker not found." in caplog.text


# --- Tests for download_proxies ---
# This is a more complex integration test, mocking many collaborators


@patch("proxies.get_free_proxies.run_proxy_scraper_all_protocols")
@patch("proxies.get_free_proxies.include_scraped_proxies")
@patch("proxies.get_free_proxies.requests.get")
@patch("proxies.get_free_proxies.parse_github_url")
@patch("proxies.get_free_proxies.download_github_file")
@patch("builtins.open", new_callable=mock_open)
@patch("proxies.get_free_proxies.Path")
def test_download_proxies_flow(
    MockPathLib,
    mock_file_open_builtin,
    mock_dl_github_file,
    mock_parse_github,
    mock_requests_get,
    mock_include_scraped,
    mock_run_scraper,
):
    # Configure Path mock for the aggregated_proxies.txt
    mock_aggregated_file_path = MagicMock(spec=Path)
    # RAW_PROXIES_DIR is a Path object itself. Need to mock its __truediv__ if it's used.
    # If RAW_PROXIES_DIR is a string, then MockPathLib(RAW_PROXIES_DIR) is called.
    # Assuming RAW_PROXIES_DIR is a Path object from paths.py

    # If RAW_PROXIES_DIR is a Path object, then MockPathLib itself is not called for it.
    # Instead, its methods like __truediv__ would be called.
    # For simplicity, let's assume download_proxies uses Path(RAW_PROXIES_DIR) or similar internally
    # if it needs to construct a Path object from a string.
    # Or, it might use RAW_PROXIES_DIR directly if it's already a Path object.
    # Let's mock the construction: Path(RAW_PROXIES_DIR) / "aggregated_proxies.txt"

    # We need to ensure that when Path(RAW_PROXIES_DIR) is called (if it is),
    # its subsequent __truediv__ returns our mock_aggregated_file_path.
    # This requires a more careful setup of MockPathLib if RAW_PROXIES_DIR is a string.
    # If RAW_PROXIES_DIR is a Path, then we need to patch RAW_PROXIES_DIR itself.

    # Let's patch RAW_PROXIES_DIR directly for this specific test.
    with patch("proxies.get_free_proxies.RAW_PROXIES_DIR", spec=Path) as mock_raw_proxies_dir_path_obj:
        mock_raw_proxies_dir_path_obj.__truediv__.return_value = mock_aggregated_file_path

        # Mock return values for collaborators
        mock_scraped_proxy_file = MagicMock(spec=Path, name="scraped_file1.txt")
        mock_run_scraper.return_value = [mock_scraped_proxy_file]

        mock_static_response = MagicMock()
        mock_static_response.status_code = 200
        mock_static_response.text = "static_proxy1:8080\nstatic_proxy2:8000"
        mock_requests_get.return_value = mock_static_response

        mock_parse_github.return_value = ("owner/repo", "file.txt")
        mock_dl_github_file.return_value = "github_proxy1:80\ngithub_proxy2:88"

        mock_outfile_handle = mock_file_open_builtin.return_value
        mock_outfile_handle.write = MagicMock()

        static_urls_to_test = ["http://static1.com/proxies.txt"]
        github_urls_to_test = ["https://github.com/user/repo/blob/main/proxies.txt"]

        result_path = download_proxies(static_urls_to_test, github_urls_to_test)

        mock_run_scraper.assert_called_once_with(PROXY_PROTOCOLS)
        mock_include_scraped.assert_called_once_with(mock_scraped_proxy_file, ANY, mock_outfile_handle)

        mock_requests_get.assert_called_once_with(static_urls_to_test[0], timeout=10)

        mock_parse_github.assert_called_once_with(github_urls_to_test[0])
        mock_dl_github_file.assert_called_once_with("owner/repo", "file.txt")

        expected_writes = [
            call("static_proxy1:8080\n"),
            call("static_proxy2:8000\n"),
            call("github_proxy1:80\n"),
            call("github_proxy2:88\n"),
        ]
        # Order of writes from different sources might not be guaranteed if sets are involved before writing.
        # However, within a source, order should be preserved.
        # For this test, let's assume include_scraped_proxies is called first, then static, then github.
        # If include_scraped_proxies also writes, its calls should be included too.
        # Since include_scraped_proxies is fully mocked, its write calls are not directly on mock_outfile_handle here.
        # This test checks writes made directly by download_proxies loop.
        for expected_call in expected_writes:
            assert expected_call in mock_outfile_handle.write.call_args_list

        assert result_path == mock_aggregated_file_path
        mock_file_open_builtin.assert_called_once_with(mock_aggregated_file_path, "w", encoding="utf-8")


@patch("proxies.get_free_proxies.run_proxy_scraper_all_protocols", return_value=[])
@patch("proxies.get_free_proxies.include_scraped_proxies")
@patch("proxies.get_free_proxies.requests.get")
@patch("proxies.get_free_proxies.parse_github_url")
@patch("proxies.get_free_proxies.download_github_file")
@patch("builtins.open", new_callable=mock_open)
@patch("proxies.get_free_proxies.RAW_PROXIES_DIR", spec=Path)  # Mock the Path object from paths.py
def test_download_proxies_static_url_fails(
    mock_raw_proxies_dir_path_obj,
    mock_file_open_builtin,
    mock_dl_github_file,
    mock_parse_github,
    mock_requests_get,
    mock_include_scraped,
    mock_run_scraper,
    caplog,
):
    mock_aggregated_file_path = MagicMock(spec=Path)
    mock_raw_proxies_dir_path_obj.__truediv__.return_value = mock_aggregated_file_path

    mock_outfile_handle = mock_file_open_builtin.return_value
    mock_outfile_handle.write = MagicMock()

    mock_requests_get.side_effect = requests.exceptions.RequestException("Connection error")

    static_urls_to_test = ["http://static_fail.com/proxies.txt"]
    github_urls_to_test = []

    download_proxies(static_urls_to_test, github_urls_to_test)

    # Check that the error was printed (current implementation uses print)
    # This is a bit fragile. If logging was used, caplog.text would be better.
    # For now, just ensure the function completes without error and other parts are called.
    # A more robust way would be to patch 'print' or refactor to use logging.

    mock_run_scraper.assert_called_once_with(PROXY_PROTOCOLS)
    mock_include_scraped.assert_not_called()  # Since run_scraper returns []
    mock_outfile_handle.write.assert_not_called()  # No successful fetches, no scraped


@patch("proxies.get_free_proxies.run_proxy_scraper_all_protocols", return_value=[])
@patch("proxies.get_free_proxies.include_scraped_proxies")
@patch("proxies.get_free_proxies.requests.get")
@patch("proxies.get_free_proxies.parse_github_url")
@patch("proxies.get_free_proxies.download_github_file")
@patch("builtins.open", new_callable=mock_open)
@patch("proxies.get_free_proxies.RAW_PROXIES_DIR", spec=Path)
def test_download_proxies_github_url_fails(
    mock_raw_proxies_dir_path_obj,
    mock_file_open_builtin,
    mock_dl_github_file,
    mock_parse_github,
    mock_requests_get,
    mock_include_scraped,
    mock_run_scraper,
    caplog,
):
    mock_aggregated_file_path = MagicMock(spec=Path)
    mock_raw_proxies_dir_path_obj.__truediv__.return_value = mock_aggregated_file_path

    mock_outfile_handle = mock_file_open_builtin.return_value
    mock_outfile_handle.write = MagicMock()

    mock_static_response = MagicMock()
    mock_static_response.status_code = 200
    mock_static_response.text = ""
    mock_requests_get.return_value = mock_static_response

    github_url_to_test = "https://github.com/user/fail_repo/blob/main/proxies.txt"
    mock_parse_github.return_value = ("user/fail_repo", "proxies.txt")
    mock_dl_github_file.side_effect = Exception("GitHub API Error")

    download_proxies([], [github_url_to_test])

    mock_outfile_handle.write.assert_not_called()
