import logging
import socket
import subprocess
import time
from pathlib import Path
from typing import Optional

from paths import MUBENG_EXECUTABLE_PATH

logger = logging.getLogger(__name__)


def find_free_port() -> int:
    """Finds a free port on localhost."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def start_mubeng_rotator_server(
    live_proxy_file: Path,
    desired_port: int,
    mubeng_timeout: str = "15s",
    country_codes: Optional[list[str]] = None,
) -> Optional[subprocess.Popen]:
    """Starts the mubeng proxy rotator server as a background process.

    Uses Solution F configuration:
    - `-w` flag: Watch proxy file for changes, auto-reload on modification
    - No `--rotate-on-error`: We handle retries manually with X-Proxy-Offset

    Args:
        live_proxy_file: Path to file containing proxy URLs (one per line)
        desired_port: Port to run the rotator on (e.g., 8089)
        mubeng_timeout: Timeout for proxy requests (default: 15s)
        country_codes: Optional list of country codes to filter by (e.g., ["US", "DE"])

    Returns the Popen object if successful, None otherwise.
    """
    if not live_proxy_file.exists() or live_proxy_file.stat().st_size == 0:
        logger.error(
            f"Mubeng Rotator: Live proxy file {live_proxy_file} is empty or does not exist. Cannot start server."
        )
        return None

    mubeng_command = [
        str(MUBENG_EXECUTABLE_PATH),
        "-a",
        f"localhost:{desired_port}",
        "-f",
        str(live_proxy_file),
        "-w",  # Watch for file changes - auto-reload on modification (Solution F)
        "-m",
        "random",
        "-t",
        mubeng_timeout,
        "-s",  # Sync flag for more predictable rotation
    ]

    # Add country code filter if specified
    if country_codes:
        mubeng_command.extend(["--only-cc", ",".join(country_codes)])
    logger.info(f"Mubeng Rotator: Starting server with command: {' '.join(mubeng_command)}")
    try:
        # Start mubeng as a background process.
        # stdout and stderr can be redirected if needed, e.g., to subprocess.PIPE or log files.
        process = subprocess.Popen(mubeng_command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        time.sleep(1)  # Give it a second to start up / fail fast

        if process.poll() is not None:  # Check if process terminated immediately
            stderr_output = process.stderr.read().decode("utf-8") if process.stderr else "N/A"
            logger.error(
                f"Mubeng Rotator: Failed to start. Process terminated with code "
                f"{process.returncode}. Stderr: {stderr_output}"
            )
            return None

        logger.info(f"Mubeng Rotator: Server started successfully on localhost:{desired_port}, PID: {process.pid}")
        return process
    except FileNotFoundError:
        logger.error(f"Mubeng Rotator: Failed. Executable not found at {MUBENG_EXECUTABLE_PATH}")
        return None
    except Exception as e:
        logger.error(f"Mubeng Rotator: An unexpected error occurred while starting: {e}", exc_info=True)
        return None


def stop_mubeng_rotator_server(process: subprocess.Popen):
    """Stops the mubeng proxy rotator server process."""
    if process and process.poll() is None:  # Check if process is still running
        logger.info(f"Mubeng Rotator: Stopping server (PID: {process.pid})...")
        try:
            process.terminate()
            process.wait(timeout=5)  # Wait for graceful termination
            logger.info(f"Mubeng Rotator: Server (PID: {process.pid}) terminated.")
        except subprocess.TimeoutExpired:
            logger.warning(f"Mubeng Rotator: Server (PID: {process.pid}) did not terminate gracefully, killing...")
            process.kill()
            process.wait()
            logger.info(f"Mubeng Rotator: Server (PID: {process.pid}) killed.")
        except Exception as e:
            logger.error(f"Mubeng Rotator: Error stopping server (PID: {process.pid}): {e}", exc_info=True)
    elif process:
        logger.info(
            f"Mubeng Rotator: Server (PID: {process.pid}) was already stopped (return code: {process.returncode})."
        )
    else:
        logger.info("Mubeng Rotator: Stop called but no process was provided or it was already None.")


