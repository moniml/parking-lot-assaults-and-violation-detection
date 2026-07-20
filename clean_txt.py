import os

folders = [
    r"D:\parking lot\extracted_frames\train\Fight",
    r"D:\parking lot\extracted_frames\train\NonFight",
    r"D:\parking lot\extracted_frames\val\Fight",
    r"D:\parking lot\extracted_frames\val\NonFight"
]

total_deleted = 0

for folder in folders:
    print(f"\nCleaning: {folder}")

    if not os.path.exists(folder):
        print("Folder not found, skipping")
        continue

    for file in os.listdir(folder):
        if file.endswith(".txt"):
            file_path = os.path.join(folder, file)
            os.remove(file_path)
            total_deleted += 1
            print("Deleted:", file)

print(f"\n✅ DONE — Total TXT files deleted: {total_deleted}")
