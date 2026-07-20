import cv2
import os

# Dataset configuration
datasets = [

    {
        "input_folder": r"RWF-2000/train/Fight",
        "output_folder": r"extracted_frames/train/Fight",
        "limit": 250,
        "prefix": "train_fight"
    },

    {
        "input_folder": r"RWF-2000/train/NonFight",
        "output_folder": r"extracted_frames/train/NonFight",
        "limit": 250,
        "prefix": "train_nonfight"
    },

    {
        "input_folder": r"RWF-2000/val/Fight",
        "output_folder": r"extracted_frames/val/Fight",
        "limit": 100,
        "prefix": "val_fight"
    },

    {
        "input_folder": r"RWF-2000/val/NonFight",
        "output_folder": r"extracted_frames/val/NonFight",
        "limit": 100,
        "prefix": "val_nonfight"
    }
]

# Start extraction
for data in datasets:

    input_folder = data["input_folder"]
    output_folder = data["output_folder"]
    limit = data["limit"]
    prefix = data["prefix"]

    # Create output folder
    os.makedirs(output_folder, exist_ok=True)

    saved_count = 0

    print(f"\nProcessing Folder: {input_folder}")

    # Loop through videos
    for video_name in os.listdir(input_folder):

        video_path = os.path.join(input_folder, video_name)

        cap = cv2.VideoCapture(video_path)

        frame_count = 0

        while True:

            success, frame = cap.read()

            if not success:
                break

            # Save every 20th frame
            if frame_count % 20 == 0:

                frame_name = f"{prefix}_{saved_count}.jpg"

                frame_path = os.path.join(
                    output_folder,
                    frame_name
                )

                cv2.imwrite(frame_path, frame)

                print("Saved:", frame_name)

                saved_count += 1

            frame_count += 1

            # Stop when limit reached
            if saved_count >= limit:
                break

        cap.release()

        if saved_count >= limit:
            break

    print(f"\nCompleted {prefix} -> {saved_count} frames")

print("\nALL 700 FRAMES EXTRACTED SUCCESSFULLY")