# Parking Lot Assault & Violation Detection using YOLOv26

A Computer Vision project that detects assault and suspicious activities in parking lot surveillance videos using a custom-trained YOLOv26 model. The application provides real-time object detection through a Flask-based web interface.

## Features

- Real-time assault detection from surveillance videos
- Upload and analyze videos through a Flask web application
- Bounding box visualization for detected incidents
- Custom-trained YOLOv26 model
- Lightweight and fast inference
- User-friendly web interface

## Tech Stack

- Python
- YOLOv26
- OpenCV
- Flask
- Google Colab
- Git & GitHub
- LabelMe

## Dataset

- **Dataset:** RWF-2000 (Real-World Fight Dataset)
- Frame extraction from fight videos
- Manual annotation using **LabelMe**
- Labels converted to YOLO format for training

## Project Workflow

1. Collect RWF-2000 dataset
2. Extract frames from videos
3. Annotate images using LabelMe
4. Convert annotations to YOLO format
5. Train YOLOv26 model
6. Save the best trained weights
7. Integrate the model with Flask
8. Upload videos and perform detection

## Folder Structure

```
Parking-Lot-Assault-and-Violation-Detection/
│── static/
│── templates/
│── server.py
│── predict.py
│── train.py
│── extract_frames.py
│── split_dataset.py
│── convert.py
│── clean_txt.py
│── make_dirs.py
│── requirements.txt
│── README.md
```

## Installation

Clone the repository

```bash
git clone https://github.com/moniml/parking-lot-assaults-and-violation-detection.git
```

Move into the project directory

```bash
cd parking-lot-assaults-and-violation-detection
```

Install dependencies

```bash
pip install -r requirements.txt
```

## Run the Project

```bash
python server.py
```

Open your browser and visit

```
http://127.0.0.1:5000
```

## Results

- Successfully trained a custom YOLOv26 model
- Detects assault-related activities in surveillance footage
- Provides bounding box visualization of detected events
- Deployable using a Flask web application

## Learning Outcomes

- Computer Vision
- Object Detection
- Dataset Preparation
- Image Annotation
- YOLO Training
- Flask Deployment
- Model Evaluation
- Git & GitHub

## Future Improvements

- Live CCTV integration
- Multiple violation detection
- Person tracking
- Alert notification system
- Cloud deployment

## Acknowledgement

This project was developed as part of my **MLOps Training** under the guidance of **Mr. Kishore**. It provided hands-on experience in dataset preparation, annotation, object detection model training, and deployment.

## Author

**Monica M**
AI & Machine Learning Student
Sri Shakthi Institute of Engineering and Technology

GitHub: https://github.com/moniml
LinkedIn: www.linkedin.com/in/monica-m-79a859289
