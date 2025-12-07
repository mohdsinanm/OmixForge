import os, subprocess
from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

def run_shell_command(command: str) -> str:
    """Runs a shell command and returns its output as a string."""
    try:
        logger.info(f"Executing command: {command}")
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command '{command}': {e.stderr}")
        return None

def run_shell_command_stream(command: str):
    """Return (process, generator) to stream output lines."""
    try:
        logger.info(f"Executing command: {command}")

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        def stream():
            for line in iter(process.stdout.readline, ''):
                yield line.strip()
            process.stdout.close()

        return process, stream()

    except Exception as e:
        logger.error(f"Error executing command '{command}': {str(e)}")
        return None, iter(())