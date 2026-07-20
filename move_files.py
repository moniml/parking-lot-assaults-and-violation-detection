import os
import shutil

# Create YOLO folder structure
folders = [
    "dataset/images/train",
    "dataset/images/val",
    "dataset/labels/train",
    "dataset/labels/val"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

# SOURCE FOLDERS
train_folder = r"extracted_frames/train/Fight"
val_folder = r"extracted_frames/val/Fight"

# MOVE TRAIN FILES
for file in os.listdir(train_folder):

    source_path = os.path.join(train_folder, file)

    # Move images
    if file.endswith(".jpg"):
        destination = os.path.join(
            "dataset/images/train",
            file
        )
        shutil.copy(source_path, destination)

    # Move labels
    elif file.endswith(".txt"):
        destination = os.path.join(
            "dataset/labels/train",
            file
        )
        shutil.copy(source_path, destination)

# MOVE VALIDATION FILES
for file in os.listdir(val_folder):

    source_path = os.path.join(val_folder, file)

    # Move images
    if file.endswith(".jpg"):
        destination = os.path.join(
            "dataset/images/val",
            file
        )
        shutil.copy(source_path, destination)

    # Move labels
    elif file.endswith(".txt"):
        destination = os.path.join(
            "dataset/labels/val",
            file
        )
        shutil.copy(source_path, destination)

print("ALL FILES MOVED SUCCESSFULLY")