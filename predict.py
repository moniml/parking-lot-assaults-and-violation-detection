from ultralytics import YOLO

model = YOLO("best.pt")

results = model.predict(
    source=r"D:\parking lot\dataset\images\train",
    conf=0.25,
    save=True,
    project=r"D:\parking lot\runs",
    name="train_predictions"
)

print("Done")