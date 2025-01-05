import cv2
import numpy as np
import math
import sqlite3
import logging
from datetime import datetime
from flask import Flask, render_template_string, jsonify

# Configure logging
logging.basicConfig(
    filename="dartboard_score_calc.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Flask app setup
app = Flask(__name__)

# Database setup
DB_FILE = "dart_scores.db"

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
        print(f"Logged score: {score} at {timestamp}")
    except sqlite3.Error as e:
        logging.error(f"Error logging score to database: {e}")
        raise

def calculate_score(x, y, center_x, center_y, radius):
    """Calculate the dart score based on dartboard position."""
    # Calculate polar coordinates relative to dartboard center
    dx, dy = x - center_x, y - center_y
    distance = math.sqrt(dx**2 + dy**2)
    angle = (math.atan2(dy, dx) * 180 / math.pi) % 360

    # Determine score region
    if distance <= 15:  # Bullseye (inner)
        return 50
    elif distance <= 30:  # Bullseye (outer)
        return 25
    elif distance > radius:  # Outside dartboard
        return 0
    else:
        # Define score zones by angle
        angle_ranges = [
            (0, 18), (18, 36), (36, 54), (54, 72), (72, 90), (90, 108),
            (108, 126), (126, 144), (144, 162), (162, 180), (180, 198),
            (198, 216), (216, 234), (234, 252), (252, 270), (270, 288),
            (288, 306), (306, 324), (324, 342), (342, 360)
        ]
        scores = [6, 13, 4, 18, 1, 20, 5, 12, 9, 14, 11, 8, 16, 7, 19, 3, 17, 2, 15, 10]

        # Find the angle region and corresponding score
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
        return circles[0]  # Return the first detected circle (x, y, radius)
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

# Flask routes
@app.route("/")
def index():
    scores = log_score_to_database()
    return "Web UI Placeholder"

# Main function
def main():
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

            # Detect dartboard
            if dartboard_data is None:
                dartboard_data = detect_dartboard(frame)
                if dartboard_data:
                    center_x, center_y, radius = dartboard_data
                    print(f"Dartboard detected at ({center_x}, {center_y}), radius: {radius}")
                else:
                    print("No dartboard detected.")
                    continue

            # Detect and calculate scores
            if previous_frame is not None:
                dart_hits = detect_dart_hits(previous_frame, frame)
                for (x, y) in dart_hits:
                    score = calculate_score(x, y, center_x, center_y, radius)
                    log_score_to_database(score)
                    print(f"Dart hit at ({x}, {y}), Score: {score}")

            previous_frame = frame.copy()

            # Display the frame (optional)
            cv2.imshow("Dartboard Detection", frame)

            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        video_capture.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
