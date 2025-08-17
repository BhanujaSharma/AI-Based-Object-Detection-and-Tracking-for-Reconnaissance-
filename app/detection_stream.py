import cv2
import face_recognition
import numpy as np
import os
import uuid
from datetime import datetime
from app.database import collection

# Create base folder for face images if not exists
BASE_IMAGE_DIR = "app/static/images"
os.makedirs(BASE_IMAGE_DIR, exist_ok=True)

# Load known faces from MongoDB
known_encodings = []
known_ids = []

def load_known_faces_from_db():
    global known_encodings, known_ids
    known_encodings.clear()
    known_ids.clear()

    records = collection.find({})
    for record in records:
        if 'encoding' in record and 'entity_id' in record:
            known_encodings.append(np.array(record['encoding']))
            known_ids.append(record['entity_id'])

load_known_faces_from_db()

def generate_frames(zone: str):
    cap = cv2.VideoCapture(0)  # You can modify this for other camera inputs

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Resize frame to speed up face recognition
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]  # BGR to RGB

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
            face_distances = face_recognition.face_distance(known_encodings, face_encoding)

            if True in matches:
                best_match_index = np.argmin(face_distances)
                entity_id = known_ids[best_match_index]
            else:
                # It's a new face
                entity_id = str(uuid.uuid4())[:8]  # Short unique ID
                known_encodings.append(face_encoding)
                known_ids.append(entity_id)

                # Save cropped face image
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                face_image = frame[top:bottom, left:right]

                # Create zone folder
                zone_folder = os.path.join(BASE_IMAGE_DIR, zone)
                os.makedirs(zone_folder, exist_ok=True)

                image_filename = f"{entity_id}.jpg"
                image_path = os.path.join(zone_folder, image_filename)
                cv2.imwrite(image_path, face_image)

                # Save to MongoDB
                collection.insert_one({
                    "entity_id": entity_id,
                    "encoding": face_encoding.tolist(),
                    "timestamp": datetime.now(),
                    "zone": zone,
                    "image_path": f"/static/images/{zone}/{image_filename}"
                })

            # Annotate frame with entity ID
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {entity_id}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

        # Encode frame and yield to client
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
