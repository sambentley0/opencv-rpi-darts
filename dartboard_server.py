import cv2
import numpy as np
import math
import os
import sqlite3
import logging
from datetime import datetime
from flask import Flask, render_template_string, jsonify, Response

# Configure output directory
OUTPUT_DIR = "/home/pi/dartboard_data"  # Change this to your preferred location
os.makedirs(OUTPUT_DIR, exist_ok=True)  # Create directory if it doesn't exist

# Configure logging
LOG_FILE = os.path.join(OUTPUT_DIR, "dartboard_score_calc.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Flask app setup
app = Flask(__name__)

# Database setup
DB_FILE = os.path.join(OUTPUT_DIR, "dart_scores.db")

def setup_database():
    """Create the database and table if they don't exist."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                score INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Database setup error: {e}")
        raise

def log_score_to_database(score):
    """Log a detected score to the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute("INSERT INTO scores (score, timestamp) VALUES (?, ?)", (score, timestamp))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Error logging score to database: {e}")
        raise

def calculate_score(x, y, center_x, center_y, radius):
    """Calculate the dart score based on dartboard position."""
    dx, dy = x - center_x, y - center_y
    distance = math.sqrt(dx**2 + dy**2)
    angle = (math.atan2(dy, dx) * 180 / math.pi) % 360

    if distance <= 15:  # Bullseye (inner)
        return 50
    elif distance <= 30:  # Bullseye (outer)
        return 25
    elif distance > radius:  # Outside dartboard
        return 0
    else:
        angle_ranges = [
            (0, 18), (18, 36), (36, 54), (54, 72), (72, 90), (90, 108),
            (108, 126), (126, 144), (144, 162), (162, 180), (180, 198),
            (198, 216), (216, 234), (234, 252), (252, 270), (270, 288),
            (288, 306), (306, 324), (324, 342), (342, 360)
        ]
        scores = [6, 13, 4, 18, 1, 20, 5, 12, 9, 14, 11, 8, 16, 7, 19, 3, 17, 2, 15, 10]

        for (start, end), score in zip(angle_ranges, scores):
            if start <= angle < end:
                if 90 < distance < 100:  # Triple ring
                    return score * 3
                elif 160 < distance < 170:  # Double ring
                    return score * 2
                return score
    return 0

def detect_dartboard(frame):
    """Detect the dartboard in the frame and return its center and radius."""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_frame, (5, 5), 0)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=100,
        param1=50,
        param2=30,
        minRadius=200,
        maxRadius=400
    )
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        return circles[0]
    return None

def detect_dart_hits(previous_frame, current_frame):
    """Detect dart hits by comparing consecutive frames."""
    frame_delta = cv2.absdiff(previous_frame, current_frame)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    hits = []
    for contour in contours:
        if cv2.contourArea(contour) > 50:  # Filter small changes
            (x, y, w, h) = cv2.boundingRect(contour)
            hits.append((x + w // 2, y + h // 2))  # Center of the dart hit
    return hits

# Flask Routes
@app.route("/")
def index():
    """Render the HTML interface for scores."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT score, timestamp FROM scores ORDER BY id DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Error fetching scores: {e}")
        rows = []

    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dartboard Scores</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin: 20px; }
            table { margin: 0 auto; border-collapse: collapse; width: 50%; }
            th, td { padding: 10px; border: 1px solid #ddd; }
            th { background-color: #f4f4f4; }
        </style>
    </head>
    <body>
        <h1>Dartboard Scores</h1>
        <a href="/video_feed">View Live Feed</a>
        <table>
            <tr><th>Score</th><th>Timestamp</th></tr>
            {% for score, timestamp in rows %}
            <tr><td>{{ score }}</td><td>{{ timestamp }}</td></tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(template, rows=rows)

@app.route("/video_feed")
def video_feed():
    """Stream video from the camera."""
    return Response(generate_video_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")

def generate_video_stream():
    """Yield frames for video streaming."""
    global video_capture
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

# Main Script
video_capture = None

def main():
    global video_capture
    setup_database()
    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        logging.error("Unable to access the webcam.")
        raise RuntimeError("Unable to access the webcam. Ensure it is connected and not in use.")

    previous_frame = None
    dartboard_data = None

    print("Starting dartboard detection. Press 'q' to quit.")
    try:
        while True:
            ret, frame = video_capture.read()
            if not ret:
                logging.error("Failed to read frame from webcam.")
                break

            if dartboard_data is None:
                dartboard_data = detect_dartboard(frame)
                if dartboard_data:
                    center_x, center_y, radius = dartboard_data
                    print(f"Dartboard detected at ({center_x}, {center_y}), radius: {radius}")
                else:
                    print("No dartboard detected.")
                    continue

            if previous_frame is not None:
                dart_hits = detect_dart_hits(previous_frame, frame)
                for (x, y) in dart_hits:
                    score = calculate_score(x, y, center_x, center_y, radius)
                    log_score_to_database(score)
                    print(f"Dart hit at ({x}, {y}), Score: {score}")

            previous_frame = frame.copy()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        video_capture.release()

if __name__ == "__main__":
    import threading
    setup_database()

    # Run the Flask server on a separate thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False)).start()

    # Run the main script
    main()
