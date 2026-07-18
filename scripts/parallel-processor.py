#!/usr/bin/env python3
import time
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run_cmd(cmd):
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    return res.returncode == 0

def main():
    print("🚀 Starting parallel processor loop...")
    while True:
        # Check if there are any PDFs in downloads
        pdf_dir = ROOT / "pdf-local" / "downloads"
        pdfs = list(pdf_dir.glob("*.pdf"))
        print(f"Found {len(pdfs)} PDFs in downloads.")
        
        if len(pdfs) == 0:
            print("No PDFs found. Sleeping for 15 seconds...")
            time.sleep(15)
            continue

        print("--- Running Batch Conversion ---")
        run_cmd([sys.executable, "scripts/batch-convert-local.py"])

        print("--- Running Process Incoming ---")
        run_cmd([sys.executable, "scripts/process-incoming.py"])

        print("--- Running Validate Metadata ---")
        run_cmd([sys.executable, "scripts/validate-metadata.py"])

        print("--- Running Generate Index ---")
        run_cmd([sys.executable, "scripts/generate-index.py"])

        print("Batch processed. Sleeping for 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    main()
