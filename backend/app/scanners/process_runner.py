"""
Safe asynchronous process execution and tool availability detection for AegisScan scanners.
"""

import asyncio
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger


def check_tool_available(tool_name: str, custom_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Detect whether a binary/tool is available on the host system.
    Returns (is_available, resolved_executable_path).
    """
    # 1. Check custom path if explicitly configured
    if custom_path:
        custom_p = Path(custom_path)
        if custom_p.is_file() and os.access(str(custom_p), os.X_OK):
            return True, str(custom_p)
        if shutil.which(custom_path):
            return True, shutil.which(custom_path)

    # 2. Check system PATH
    resolved = shutil.which(tool_name)
    if resolved:
        return True, resolved

    # 3. Check common Windows / Linux binary variants
    variants = [
        f"{tool_name}.exe",
        f"{tool_name}.bat",
        f"{tool_name}.cmd",
        f"{tool_name}.sh"
    ]
    for v in variants:
        found = shutil.which(v)
        if found:
            return True, found

    return False, None


class ProcessExecutionResult:
    """Encapsulates process run outputs."""
    def __init__(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_seconds: float,
        timed_out: bool = False,
        cancelled: bool = False
    ):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration_seconds = duration_seconds
        self.timed_out = timed_out
        self.cancelled = cancelled



# Public name retained for scanner integrations and test doubles.
SafeProcessResult = ProcessExecutionResult


async def run_safe_process(
    cmd_args: List[str],
    cwd: Optional[str] = None,
    timeout: int = 120,
    env: Optional[Dict[str, str]] = None
) -> ProcessExecutionResult:
    """
    Safely execute a command using argument arrays (preventing shell injection),
    enforcing timeouts and capturing stdout/stderr safely.
    """
    if not cmd_args:
        raise ValueError("Cannot execute empty command arguments")

    start_time = time.time()
    exec_env = os.environ.copy()
    if env:
        exec_env.update(env)

    logger.info(f"PROCESS_SPAWN: cmd='{cmd_args[0]}' args={cmd_args[1:]} cwd='{cwd}' timeout={timeout}s")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=exec_env
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=float(timeout)
            )
            duration = round(time.time() - start_time, 2)
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            logger.info(f"PROCESS_EXIT: cmd='{cmd_args[0]}' exit_code={process.returncode} duration={duration}s")
            return ProcessExecutionResult(
                exit_code=process.returncode or 0,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                timed_out=False,
                cancelled=False
            )

        except asyncio.TimeoutError:
            logger.warning(f"PROCESS_TIMEOUT: cmd='{cmd_args[0]}' exceeded {timeout}s timeout. Terminating...")
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=1)
                if process.returncode is None:
                    process.kill()
                    await process.wait()
            except Exception as kill_err:
                logger.debug(f"Process termination error: {kill_err}")

            # Drain pipes after termination so child-process output is not left open.
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=1)
            except Exception:
                stdout_bytes, stderr_bytes = b"", b""

            duration = round(time.time() - start_time, 2)
            return ProcessExecutionResult(
                exit_code=-1,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=(stderr_bytes.decode("utf-8", errors="replace") +
                        f"\nProcess timed out after {timeout} seconds and was terminated.").strip(),
                duration_seconds=duration,
                timed_out=True,
                cancelled=False
            )

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        logger.error(f"PROCESS_EXEC_FAILED: cmd='{cmd_args[0]}' error: {e}")
        return ProcessExecutionResult(
            exit_code=-1,
            stdout="",
            stderr=str(e),
            duration_seconds=duration,
            timed_out=False,
            cancelled=False
        )
