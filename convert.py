import os
import json

root = r"D:\parking lot\extracted_frames"
output_labels = r"D:\parking lot\dataset\labels"

os.makedirs(output_labels, exist_ok=True)

class_map = {
    "normal": 0,
    "suspicious": 1,
    "violation": 2,
    "assault": 3
}

def convert(json_path, out_path):

    with open(json_path, "r") as f:
        data = json.load(f)

    w = data["imageWidth"]
    h = data["imageHeight"]

    lines = []

    print("Processing:", json_path)

    for shape in data["shapes"]:

        label = shape["label"]

        if label not in class_map:
            print("Skipping unknown label:", label)
            continue

        class_id = class_map[label]

        x1, y1 = shape["points"][0]
        x2, y2 = shape["points"][1]

        # YOLO format
        x_center = ((x1 + x2) / 2) / w
        y_center = ((y1 + y2) / 2) / h
        width = abs(x2 - x1) / w
        height = abs(y2 - y1) / h

        lines.append(f"{class_id} {x_center} {y_center} {width} {height}")

    # 🚫 skip empty files
    if len(lines) == 0:
        print("No labels found:", json_path)
        return

    with open(out_path, "w") as f:
        f.write("\n".join(lines))


for folder in ["train/Fight", "train/NonFight", "val/Fight", "val/NonFight"]:

    path = os.path.join(root, folder)

    if not os.path.exists(path):
        continue

    for file in os.listdir(path):

        if file.endswith(".json"):

            json_path = os.path.join(path, file)

            txt_name = file.replace(".json", ".txt")
            out_path = os.path.join(output_labels, txt_name)

            convert(json_path, out_path)

print("✅ DONE")