import re
import json
from pathlib import Path


_EXIT_CODE_PATTERN = re.compile(r"<<exit-code:([^>]+)>>", re.IGNORECASE)


def classify_run_log(log_content: str) -> str:
    """Classify a run by its final recorded exit code, with legacy log fallback."""
    normalized = (log_content or "").casefold()
    exit_codes = _EXIT_CODE_PATTERN.findall(log_content or "")

    if exit_codes:
        final_code = exit_codes[-1].strip().casefold()
        if final_code == "interrupted":
            return "Interrupted"
        try:
            exit_code = int(final_code)
        except ValueError:
            return "Failed"
        if exit_code == 0:
            return "Completed"
        if exit_code == 143:
            return "Cancelled"
        return "Failed"

    if "pipeline run cancelled by user" in normalized:
        return "Cancelled"
    if "running pipeline:" in normalized:
        return "Running"
    return "Unknown"


def is_private_run(run_name: str, run_dir) -> bool:
    """Recognize private runs from a durable marker or their run metadata/archive."""
    base_name = Path(str(run_name)).name
    for suffix in (".txt", ".tar.gz.enc"):
        if base_name.endswith(suffix):
            base_name = base_name[:-len(suffix)]
            break

    root = Path(run_dir)
    marker = root / ".private_runs" / f"{base_name}.json"
    if marker.exists():
        return True
    if (root / f"{base_name}.tar.gz.enc").exists():
        return True
    metadata_path = root / base_name / "omixforge-run.json"
    try:
        return bool(json.loads(metadata_path.read_text(encoding="utf-8")).get("encrypted"))
    except (OSError, ValueError, TypeError):
        return False
