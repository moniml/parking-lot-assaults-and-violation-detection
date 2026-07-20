import os
import time
import json
import tempfile

# Force temporary uploads/buffering to use the D: drive workspace (avoids C: drive space limits)
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(WORKSPACE_DIR, 'temp_uploads', 'tmp')
os.makedirs(TMP_DIR, exist_ok=True)
tempfile.tempdir = TMP_DIR
os.environ['TEMP'] = TMP_DIR
os.environ['TMP'] = TMP_DIR

from flask import Flask, render_template, Response, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import cv2
from ultralytics import YOLO

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configure upload folder
UPLOAD_FOLDER = os.path.join(WORKSPACE_DIR, 'temp_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set allowed video extensions
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'avi', 'mkv'}

# Load YOLO Model
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'best.pt')
if not os.path.exists(MODEL_PATH):
    # Fallback to yolov8n if best.pt is somehow not found
    MODEL_PATH = "yolov8n.pt"

print(f"Loading YOLO model from: {MODEL_PATH}")
model = YOLO(MODEL_PATH)

# Class mappings
CLASS_NAMES = {
    0: "Normal",
    1: "Suspicious",
    2: "Violation",
    3: "Assault"
}

# Neon RGB colors for bounding boxes
CLASS_COLORS = {
    0: (0, 255, 102),    # Neon Green
    1: (255, 159, 0),    # Neon Orange/Yellow
    2: (255, 0, 85),     # Neon Pink/Red
    3: (255, 0, 0)       # Deep Threat Red
}

# Global dictionary to store the latest telemetric state
current_telemetry = {
    "fps": 0,
    "detections": [],
    "threat_score": 0,
    "status": "System Operational",
    "active_counts": {
        "Normal": 0,
        "Suspicious": 0,
        "Violation": 0,
        "Assault": 0
    }
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_default_video():
    # Find a default video from RWF-2000 val set or use a dummy stream if not found
    val_fight_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'RWF-2000', 'val', 'Fight')
    if os.path.exists(val_fight_dir):
        files = [f for f in os.listdir(val_fight_dir) if f.endswith('.avi')]
        if files:
            # Let's pick a nice size one, e.g. 1Kbw1bUw_0.avi
            if "1Kbw1bUw_0.avi" in files:
                return os.path.join(val_fight_dir, "1Kbw1bUw_0.avi")
            return os.path.join(val_fight_dir, files[0])
    return None

def draw_cyberpunk_bbox(img, x1, y1, x2, y2, label, confidence, color, track_id=None):
    # Semi-transparent overlay fill
    overlay = img.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
    # Blend overlay with original (opacity 15%)
    cv2.addWeighted(overlay, 0.15, img, 0.85, 0, img)
    
    # Draw outer thin neon box
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)
    
    # Draw thicker neon corner brackets
    d = min(15, int((x2 - x1) * 0.2), int((y2 - y1) * 0.2)) # Bracket length
    t = 3 # Thickness
    
    # Top-Left Corner
    cv2.line(img, (x1, y1), (x1 + d, y1), color, t)
    cv2.line(img, (x1, y1), (x1, y1 + d), color, t)
    
    # Top-Right Corner
    cv2.line(img, (x2, y1), (x2 - d, y1), color, t)
    cv2.line(img, (x2, y1), (x2, y1 + d), color, t)
    
    # Bottom-Left Corner
    cv2.line(img, (x1, y2), (x1 + d, y2), color, t)
    cv2.line(img, (x1, y2), (x1, y2 - d), color, t)
    
    # Bottom-Right Corner
    cv2.line(img, (x2, y2), (x2 - d, y2), color, t)
    cv2.line(img, (x2, y2), (x2, y2 - d), color, t)
    
    # Futuristic HUD Label
    text = f"{label.upper()} {confidence:.0%}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.4
    thickness = 1
    
    # Get text width & height
    (w, h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    # Draw text background banner
    cv2.rectangle(img, (x1, y1 - h - 6), (x1 + w + 8, y1), color, -1)
    
    # Write black text inside neon banner
    cv2.putText(img, text, (x1 + 4, y1 - 4), font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA)

def get_final_condition(class_frequency):
    if class_frequency.get("Assault", 0) > 0:
        return "ASSAULT ACTIVITY"
    elif class_frequency.get("Violation", 0) > 0:
        return "PARKING VIOLATION"
    elif class_frequency.get("Suspicious", 0) > 0:
        return "SUSPICIOUS ACTIVITY"
    else:
        return "NORMAL CONDITION"

def generate_video_stream(video_path, conf_threshold=0.25, enabled_classes=None):
    global current_telemetry
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video: {video_path}")
        return
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        total_frames = 200 # Fallback
        
    frame_index = 0
    has_completed_pass = False
    analyzed_frames_count = 0
    
    # Session summary metrics
    class_frequency = {"Normal": 0, "Suspicious": 0, "Violation": 0, "Assault": 0}
    peak_threat_score = 0
    final_condition_result = "NORMAL CONDITION"
    
    fps_time = time.time()
    fps_counter = 0
    fps_display = 0
    
    # Default to all classes if not specified
    if enabled_classes is None:
        enabled_classes = {0, 1, 2, 3}
        
    while cap.isOpened():
        ret, frame = cap.read()
        frame_index += 1
        
        if not ret:
            # We reached the end of the video! Compiled overall condition
            has_completed_pass = True
            final_condition_result = get_final_condition(class_frequency)
            
            # Loop the video for surveillance feel
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_index = 0
            ret, frame = cap.read()
            if not ret:
                continue
                
        # Calculate FPS
        fps_counter += 1
        elapsed = time.time() - fps_time
        if elapsed >= 1.0:
            fps_display = int(fps_counter / elapsed)
            fps_counter = 0
            fps_time = time.time()
            
        # Resize frame for fluid streaming performance
        frame_resized = cv2.resize(frame, (854, 480))
        
        # Run YOLO inference
        results = model(frame_resized, conf=conf_threshold, verbose=False)
        
        active_detections = []
        counts = {"Normal": 0, "Suspicious": 0, "Violation": 0, "Assault": 0}
        max_threat_score = 0
        
        if len(results) > 0:
            boxes = results[0].boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                
                # Check if this class is toggled active
                if cls_id not in enabled_classes:
                    continue
                    
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()
                x1, y1, x2, y2 = map(int, xyxy)
                
                class_name = CLASS_NAMES.get(cls_id, "Unknown")
                counts[class_name] += 1
                
                # Dynamic Threat Score Calculation
                # Normal: 10, Suspicious: 35, Violation: 70, Assault: 100
                if cls_id == 0:
                    threat_val = 10
                elif cls_id == 1:
                    threat_val = 40
                elif cls_id == 2:
                    threat_val = 75
                elif cls_id == 3:
                    threat_val = 100
                else:
                    threat_val = 0
                    
                max_threat_score = max(max_threat_score, int(threat_val * conf))
                
                # Save detection info
                active_detections.append({
                    "class": class_name,
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2]
                })
                
                # Draw Cyberpunk HUD overlays
                color = CLASS_COLORS.get(cls_id, (255, 255, 255))
                draw_cyberpunk_bbox(frame_resized, x1, y1, x2, y2, class_name, conf, color)
                
        # Calculate global threat score based on detections
        threat_score = max_threat_score
        
        # Update session trackers if we haven't completed the first loop yet
        if not has_completed_pass:
            analyzed_frames_count += 1
            for cls_name, count in counts.items():
                if count > 0:
                    class_frequency[cls_name] += 1
            peak_threat_score = max(peak_threat_score, threat_score)
            
        # Determine status text
        if counts["Assault"] > 0:
            status_text = "CRITICAL THREAT: ASSAULT DETECTED"
        elif counts["Violation"] > 0:
            status_text = "WARNING: PARKING VIOLATION"
        elif counts["Suspicious"] > 0:
            status_text = "ALERT: SUSPICIOUS ACTIVITY"
        else:
            status_text = "SYSTEM SECURE"
            
        # Update global telemetry
        current_telemetry = {
            "fps": fps_display or 30,
            "detections": active_detections,
            "threat_score": threat_score,
            "status": status_text,
            "active_counts": counts,
            "timestamp": time.time(),
            "completed": has_completed_pass,
            "summary": {
                "total_frames": total_frames,
                "analyzed_frames": analyzed_frames_count,
                "class_occurrences": class_frequency,
                "peak_threat_score": peak_threat_score,
                "final_condition": final_condition_result if has_completed_pass else get_final_condition(class_frequency)
            }
        }
        
        # Draw dynamic UI HUD bar in the video frame (futuristic styling)
        hud_bar_h = 35
        cv2.rectangle(frame_resized, (0, 0), (854, hud_bar_h), (5, 0, 0), -1) # HUD bar bg
        cv2.line(frame_resized, (0, hud_bar_h), (854, hud_bar_h), (255, 59, 59), 1) # Red line separating HUD
        
        # Draw scanner effect (faint red grid horizontal laser line that scrolls)
        laser_y = int((time.time() * 100) % 445) + hud_bar_h
        overlay = frame_resized.copy()
        cv2.line(overlay, (0, laser_y), (854, laser_y), (255, 59, 59), 1)
        # Add glow below laser line
        cv2.rectangle(overlay, (0, max(hud_bar_h, laser_y - 4)), (854, min(480, laser_y + 4)), (255, 59, 59), -1)
        cv2.addWeighted(overlay, 0.1, frame_resized, 0.9, 0, frame_resized)
        
        # Overlay HUD text details on the frame
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame_resized, "SECURE CAM 01 | LIVE", (15, 22), font, 0.45, (255, 59, 59), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, f"FPS: {current_telemetry['fps']}", (200, 22), font, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, f"THREAT LEVEL: {current_telemetry['threat_score']}%", (350, 22), font, 0.45, CLASS_COLORS[3] if current_telemetry['threat_score'] > 50 else (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, f"STATUS: {current_telemetry['status'].upper()}", (550, 22), font, 0.42, (255, 59, 59) if current_telemetry['threat_score'] > 40 else (0, 255, 102), 1, cv2.LINE_AA)
        
        # Encode as JPEG
        ret, jpeg = cv2.imencode('.jpg', frame_resized)
        if not ret:
            continue
            
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
               
        # Control streaming frame rate (~30 FPS)
        time.sleep(0.03)
        
    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

import traceback

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            print("Upload Error: No file part in request.files")
            return jsonify({
                "success": False, 
                "message": "No file part in request.files",
                "error": "No file part"
            }), 400
            
        file = request.files['file']
        if file.filename == '':
            print("Upload Error: Empty filename")
            return jsonify({
                "success": False, 
                "message": "No selected file",
                "error": "No selected file"
            }), 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if not filename:
                filename = f"upload_{int(time.time())}.mp4"
            else:
                filename = f"{int(time.time())}_{filename}"
                
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure the directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Save the file
            file.save(filepath)
            print(f"File successfully uploaded and saved to: {filepath}")
            
            return jsonify({
                "success": True, 
                "message": "File uploaded successfully",
                "filepath": filepath,
                "data": {"filepath": filepath}
            }), 200
            
        print(f"Upload Error: Unsupported file format for filename '{file.filename}'")
        return jsonify({
            "success": False, 
            "message": f"Unsupported file format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            "error": "Unsupported file format"
        }), 400
        
    except Exception as e:
        print("EXCEPTIONAL ERROR in /api/upload:")
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "message": f"Internal Server Error: {str(e)}",
            "error": str(e)
        }), 500

@app.route('/api/stream')
def video_feed():
    source_type = request.args.get('source', 'default')
    conf = request.args.get('conf', 0.25, type=float)
    
    # Parse enabled classes (e.g. "0,1,2,3")
    classes_str = request.args.get('classes', '0,1,2,3')
    try:
        enabled_classes = {int(x) for x in classes_str.split(',') if x != ''}
    except Exception:
        enabled_classes = {0, 1, 2, 3}
        
    if source_type == 'default':
        video_path = get_default_video()
        if not video_path:
            return jsonify({"error": "No stock video found. Please upload a surveillance video."}), 404
    else:
        # Custom uploaded file
        filepath = request.args.get('path', '')
        if os.path.exists(filepath):
            video_path = filepath
        else:
            # Fallback to stock video
            video_path = get_default_video()
            if not video_path:
                return jsonify({"error": "Video file not found."}), 404
                
    return Response(generate_video_stream(video_path, conf, enabled_classes),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/telemetry')
def get_telemetry():
    global current_telemetry
    return jsonify(current_telemetry)

if __name__ == '__main__':
    print("Starting Premium Parking Lot Surveillance UI on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
