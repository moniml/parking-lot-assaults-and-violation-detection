import os
import shutil
import random

image_root = r"D:\parking lot\extracted_frames"
label_root = r"D:\parking lot\dataset\labels"

output_img_train = r"D:\parking lot\dataset\images\train"
output_img_val = r"D:\parking lot\dataset\images\val"

output_lbl_train = r"D:\parking lot\dataset\labels\train"
output_lbl_val = r"D:\parking lot\dataset\labels\val"

os.makedirs(output_img_train, exist_ok=True)
os.makedirs(output_img_val, exist_ok=True)
os.makedirs(output_lbl_train, exist_ok=True)
os.makedirs(output_lbl_val, exist_ok=True)

# collect all images
images = []

for root, _, files in os.walk(image_root):
    for file in files:
        if file.endswith(".jpg") or file.endswith(".png"):
            images.append(os.path.join(root, file))

random.shuffle(images)

split_ratio = 0.8
split_index = int(len(images) * split_ratio)

train_images = images[:split_index]
val_images = images[split_index:]


def move_files(image_list, img_dest, lbl_dest):

    for img_path in image_list:

        filename = os.path.basename(img_path)
        name = os.path.splitext(filename)[0]

        label_path = os.path.join(label_root, name + ".txt")

        # skip if no label
        if not os.path.exists(label_path):
            continue

        shutil.copy(img_path, os.path.join(img_dest, filename))
        shutil.copy(label_path, os.path.join(lbl_dest, name + ".txt"))

        print("Moved:", filename)


print("\n--- Moving TRAIN set ---")
move_files(train_images, output_img_train, output_lbl_train)

print("\n--- Moving VAL set ---")
move_files(val_images, output_img_val, output_lbl_val)

print("\n✅ DONE: Dataset split complete")
