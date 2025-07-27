import cv2
import os
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from app.database import collection, fs
from datetime import datetime
from io import BytesIO
from PIL import Image

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# === Load YOLOv8 model ===
model = YOLO('yolov8x.pt')

# === Define object categories ===
HUMAN = ['person']
VEHICLE = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']
ANIMAL = ['cat', 'dog', 'horse', 'cow', 'sheep', 'bird']

# === DeepSORT Tracker ===
tracker = DeepSort(max_age=30)

def generate_frames():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, verbose=False)[0]
        detections = []

        for result in results.boxes.data:
            x1, y1, x2, y2, conf, cls = result
            label = model.names[int(cls)]

            if float(conf) < 0.5:
                continue

            # Map label to broader category
            if label in HUMAN:
                category = "Human"
            elif label in VEHICLE:
                category = "Vehicle"
            elif label in ANIMAL:
                category = "Animal"
            else:
                category = "Object"

            bbox = [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]
            detections.append((bbox, float(conf), label, category))

        # === Track objects ===
        tracks = tracker.update_tracks(detections, frame=frame)

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            l, t, r, b = map(int, track.to_ltrb())

            # Draw bounding box
            cv2.rectangle(frame, (l, t), (r, b), (0, 255, 0), 2)
            cv2.putText(frame, f'ID: {track_id}', (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Crop and save image
            cropped = frame[t:b, l:r]
            if cropped.size == 0:
                continue

            pil_img = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
            buffer = BytesIO()
            pil_img.save(buffer, format="JPEG")
            buffer.seek(0)

            image_id = fs.put(buffer.getvalue(), filename=f"{track_id}_{datetime.utcnow().isoformat()}.jpg")

            # Try to get matching detection to assign correct category
            matched_detection = next((d for d in detections if d[0] == list(map(int, track.to_ltwh()))), None)
            category = matched_detection[3] if matched_detection else "Unknown"

            metadata = {
                "entity_id": str(track_id),
                "category": category,
                "timestamp": datetime.utcnow(),
                "image_id": image_id,
                "zone": "zone_a"  # Optional: can be dynamic from session
            }

            collection.update_one(
                {"entity_id": str(track_id)},
                {"$setOnInsert": metadata},
                upsert=True
            )

        # Encode to MJPEG stream
        _, buffer = cv2.imencode(".jpg", frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()
