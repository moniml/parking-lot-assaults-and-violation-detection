import os

base = r"D:\parking lot\dataset"

folders = [
    "images/train",
    "images/val",
    "labels/train",
    "labels/val"
]

for f in folders:
    path = os.path.join(base, f)
    os.makedirs(path, exist_ok=True)
    print("Created:", path)

print("\nDONE")