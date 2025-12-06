#!/bin/bash
echo "[TEST] Checking installation..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "[PASS] Dependencies installed successfully."
    exit 0
else
    echo "[FAIL] Dependency installation failed."
    exit 1
fi
