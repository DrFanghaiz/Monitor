"""
Build the current desktop app with PyInstaller.

This packages the new `main.py` shell path while keeping the legacy
customtkinter path available via `--legacy`.
"""
from pathlib import Path
import shutil
import tempfile
import os
import subprocess
import sys


def main():
    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "PyInstaller is not installed in the current Python environment."
        ) from exc

    project_root = Path(__file__).resolve().parent
    spec_file = project_root / "MonitorApp.spec"
    frontend_dist = project_root / "frontend" / "dist" / "index.html"

    if not frontend_dist.exists():
        raise SystemExit(
            "frontend/dist is missing. Run `cd frontend && npm run build` first."
        )

    temp_root = Path(tempfile.gettempdir()) / "monitor_pyinstaller"
    work_dir = temp_root / "build"
    dist_dir = temp_root / "dist"
    final_dist_dir = project_root / "dist" / "MonitorApp"

    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
    if dist_dir.exists():
        shutil.rmtree(dist_dir, ignore_errors=True)
    if final_dist_dir.exists():
        shutil.rmtree(final_dist_dir, ignore_errors=True)

    os.chdir(project_root)
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--workpath",
        str(work_dir),
        "--distpath",
        str(dist_dir),
        str(spec_file),
    ]

    print("Building desktop app...")
    print("Command:", " ".join(args))
    subprocess.check_call(args)

    built_dist_dir = dist_dir / "MonitorApp"
    shutil.copytree(built_dist_dir, final_dist_dir)

    print("\nBuild completed.")
    print(f"Output: {final_dist_dir}")


if __name__ == "__main__":
    main()
