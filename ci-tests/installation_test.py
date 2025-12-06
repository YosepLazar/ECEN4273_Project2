import subprocess
import sys

print("[TEST] Checking installation...")

try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "ci-tests/requirements.txt"])
    print("[PASS] Dependencies installed successfully.")
    sys.exit(0)
except subprocess.CalledProcessError:
    print("[FAIL] Dependency installation failed.")
    sys.exit(1)
