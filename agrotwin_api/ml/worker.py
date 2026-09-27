"""Disposable inference process: optional ML imports never enter the API process."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from inference import predict_yield

if __name__ == "__main__":
    print(json.dumps(predict_yield(**json.load(sys.stdin)), allow_nan=False))
