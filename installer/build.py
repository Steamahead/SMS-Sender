"""Build SMS Sender into a distributable package using PyInstaller."""
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "SMSSender",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data", f"{os.path.join(ROOT, 'gui')}{os.pathsep}gui",
        os.path.join(ROOT, "main.py"),
    ]

    icon_path = os.path.join(ROOT, "installer", "icon.ico")
    if os.path.exists(icon_path):
        cmd.extend(["--icon", icon_path])

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True)
    print("\nBuild complete! Output in dist/SMSSender/")


if __name__ == "__main__":
    build()
