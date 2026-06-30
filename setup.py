"""
setup.py — Automated setup script for the Insurance Policy Generation Agent.

Run this once after cloning the repository:
    python setup.py

What it does:
    1. Checks Python version (3.10+ required)
    2. Creates a virtual environment (.venv)
    3. Installs all dependencies from requirements.txt
    4. Copies .env.example to .env if .env does not exist
    5. Prints next steps
"""

import sys
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
VENV = ROOT / ".venv"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
REQUIREMENTS = ROOT / "requirements.txt"


def check(condition: bool, message: str):
    if not condition:
        print(f"\n[FAIL] {message}")
        sys.exit(1)


def run(cmd: list, cwd=None):
    result = subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n[ERROR] Command failed: {' '.join(cmd)}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip()


def step(msg: str):
    print(f"\n  {msg}...")


def ok(msg: str):
    print(f"  [OK] {msg}")


def main():
    print("\n" + "=" * 60)
    print("  Insurance Policy Generation Agent — Setup")
    print("=" * 60)

    # ── 1. Python version check ────────────────────────────────────
    step("Checking Python version")
    major, minor = sys.version_info.major, sys.version_info.minor
    check(
        major == 3 and minor >= 10,
        f"Python 3.10+ required. You have Python {major}.{minor}."
    )
    ok(f"Python {major}.{minor} detected")

    # ── 2. Create virtual environment ─────────────────────────────
    step("Creating virtual environment (.venv)")
    if VENV.exists():
        ok(".venv already exists — skipping")
    else:
        run([sys.executable, "-m", "venv", str(VENV)])
        ok(".venv created")

    # ── 3. Determine pip path ─────────────────────────────────────
    if sys.platform == "win32":
        pip = str(VENV / "Scripts" / "pip.exe")
        python = str(VENV / "Scripts" / "python.exe")
    else:
        pip = str(VENV / "bin" / "pip")
        python = str(VENV / "bin" / "python")

    # ── 4. Upgrade pip ────────────────────────────────────────────
    step("Upgrading pip")
    run([pip, "install", "--upgrade", "pip", "--quiet"])
    ok("pip upgraded")

    # ── 5. Install dependencies ───────────────────────────────────
    step("Installing dependencies from requirements.txt")
    check(REQUIREMENTS.exists(), "requirements.txt not found.")
    run([pip, "install", "-r", str(REQUIREMENTS), "--quiet"])
    ok("All dependencies installed")

    # ── 6. Create .env from .env.example ─────────────────────────
    step("Setting up .env file")
    if ENV_FILE.exists():
        ok(".env already exists — skipping")
    else:
        check(ENV_EXAMPLE.exists(), ".env.example not found.")
        ENV_FILE.write_text(ENV_EXAMPLE.read_text())
        ok(".env created from .env.example")

    # ── 7. Done ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("=" * 60)

    if sys.platform == "win32":
        activate = ".venv\\Scripts\\activate"
    else:
        activate = "source .venv/bin/activate"

    env_needs_key = "your_groq_api_key_here" in ENV_FILE.read_text()

    print("\n  Next steps:\n")
    print(f"  1. Activate the virtual environment:")
    print(f"       {activate}\n")
    if env_needs_key:
        print(f"  2. Add your Groq API key to .env:")
        print(f"       GROQ_API_KEY=your_actual_key_here")
        print(f"       Get a free key at: https://console.groq.com\n")
        print(f"  3. Run the agent:")
    else:
        print(f"  2. Run the agent:")
    print(f"       python run.py\n")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
