import logging
import os
import socket
import subprocess
import time

logger = logging.getLogger(__name__)


def is_port_in_use(port: int) -> bool:
    """Check if a local port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def free_port(port: int) -> bool:
    """
    Check if a port is in use and, if so, attempt to free it by killing the process.
    Returns True if the port is free or was successfully freed, False otherwise.
    """
    if is_port_in_use(port):
        logger.warning(f"Port {port} is already in use. Attempting to free it.")
        print(f"[INFO] Port {port} is in use. Trying to free it...")
        try:
            # Find the process ID (PID) using the port
            # Using `lsof` is common on Linux/macOS.
            if os.name == "posix":
                process = subprocess.run(["lsof", "-t", f"-i:{port}"], capture_output=True, text=True, check=True)
                pid = process.stdout.strip()
                if pid:
                    logger.info(f"Found process with PID {pid} using port {port}. Killing it.")
                    print(f"[INFO] Killing process with PID: {pid}")
                    subprocess.run(["kill", "-9", pid], check=True)
                    # Wait a moment to ensure the port is released
                    time.sleep(2)
                    if not is_port_in_use(port):
                        logger.info(f"Successfully freed port {port}.")
                        print(f"[SUCCESS] Port {port} is now free.")
                        return True
                    else:
                        logger.error(f"Failed to free port {port} after killing process {pid}.")
                        print(f"[ERROR] Could not free port {port}. Please check system permissions.")
                        return False
                else:
                    logger.warning(f"lsof found no process for port {port}, but it is in use.")
                    return False
            else:
                # A placeholder for other OSes like Windows
                logger.warning("Port freeing is not implemented for this OS.")
                return False
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Failed to kill process on port {port}: {e}", exc_info=True)
            print(f"[ERROR] Failed to free port {port}. `lsof` or `kill` command may not be available.")
            return False
    else:
        logger.info(f"Port {port} is already free.")
        return True
