from ultralytics import YOLO

# Load YOLOv26 nano model
model = YOLO("yolo26n.pt")

# Train model
model.train(
    data="data.yaml",
    epochs=70,
    imgsz=640,
    batch=8
)

print("YOLOv26 TRAINING COMPLETED")