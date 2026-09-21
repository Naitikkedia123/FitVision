from pathlib import Path
import joblib
import psutil
import os

model_path = Path(
    "fitness_predictor/models/sets_model_uncompressed_TEST.joblib"
)

process = psutil.Process(os.getpid())

print("RAM before load:",
      process.memory_info().rss / (1024 ** 3), "GB")

print("Loading uncompressed model with mmap_mode='r'...")

bundle = joblib.load(model_path, mmap_mode="r")

print("LOAD SUCCESS")

print("RAM after load:",
      process.memory_info().rss / (1024 ** 3), "GB")

print("Keys:", bundle.keys())
print("Model:", type(bundle["model"]))