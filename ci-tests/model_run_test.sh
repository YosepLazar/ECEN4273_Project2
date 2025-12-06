#!/bin/bash
echo "[TEST] Running model inference..."
python main.py --test
if [ $? -eq 0 ]; then
    echo "[PASS] Model executed successfully."
    exit 0
else
    echo "[FAIL] Model failed to execute."
    exit 1
fi
