"""配布用zipファイルを作成するスクリプト.

使い方: python build_dist.py
出力:   dist/price_system.zip
"""
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
DIST_DIR = ROOT / "dist"
DIST_DIR.mkdir(exist_ok=True)

today = date.today().strftime("%Y%m%d")
ZIP_NAME = f"price_system_{today}.zip"
ZIP_PATH = DIST_DIR / ZIP_NAME

# 含めるファイル/ディレクトリ
INCLUDE = [
    "src",
    "config/rates.yaml",
    "config/settings.yaml.example",
    "pyproject.toml",
    "install.bat",
    "run_web.bat",
    "run_batch.bat",
]

# 除外パターン
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}
EXCLUDE_DIRS = {"__pycache__", ".git", ".venv", "dist", ".pytest_cache", ".egg-info"}


def should_include(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return False
        if any(part.endswith(suffix) for suffix in (".egg-info",)):
            return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    return True


def main():
    prefix = "price_system"

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in INCLUDE:
            p = ROOT / item
            if p.is_file():
                arcname = f"{prefix}/{item}"
                zf.write(p, arcname)
                print(f"  + {arcname}")
            elif p.is_dir():
                for f in sorted(p.rglob("*")):
                    if f.is_file() and should_include(f.relative_to(ROOT)):
                        arcname = f"{prefix}/{f.relative_to(ROOT)}"
                        zf.write(f, arcname)
                        print(f"  + {arcname}")

        # 掛率Excelがあれば含める
        kakuritsu = ROOT / "config" / "掛率.xlsx"
        if kakuritsu.exists():
            arcname = f"{prefix}/config/掛率.xlsx"
            zf.write(kakuritsu, arcname)
            print(f"  + {arcname}")

    print(f"\n配布用zip作成完了: {ZIP_PATH}")
    print(f"サイズ: {ZIP_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
