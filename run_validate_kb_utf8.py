import subprocess
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent
REPORT_PATH = BASE / "validate_kb_report_utf8.txt"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    result = subprocess.run(
        [sys.executable, "-X", "utf8", "validate_kb.py"],
        cwd=BASE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output = result.stdout
    if result.stderr:
        output = f"{output}\n[stderr]\n{result.stderr}".strip()

    REPORT_PATH.write_text(output + ("\n" if output and not output.endswith("\n") else ""), encoding="utf-8")
    print(output, end="" if output.endswith("\n") else "\n")
    print(f"\nREPORT_WRITTEN={REPORT_PATH}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
