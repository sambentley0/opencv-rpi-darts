import cv2
import numpy as np

def detect_dartboard(frame):
    """Detect dartboard using Hough Circles or a pre-trained model."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detect circles (dartboard boundary)
    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=50,
        param1=100,
        param2=30,
        minRadius=100,
        maxRadius=300,
    )

    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            cv2.circle(frame, (x, y), r, (0, 255, 0), 4)
            return (x, y, r)

    return None

def detect_darts(frame, dartboard_center, dartboard_radius):
    """Detect dart positions using color thresholding or edge detection."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # Define the range for detecting dart colors (e.g., red or black)
    lower_color = np.array([0, 50, 50])
    upper_color = np.array([10, 255, 255])

    mask = cv2.inRange(hsv, lower_color, upper_color)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    dart_positions = []
    for cnt in contours:
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        center = (int(x), int(y))
        radius = int(radius)
        if radius > 3:  # Filter small noise
            dart_positions.append(center)
            cv2.circle(frame, center, radius, (255, 0, 0), 3)

    return dart_positions

def calculate_score(dart_positions, dartboard_center, dartboard_radius):
    """Calculate the score based on dart positions and dartboard regions."""
    scores = []
    for pos in dart_positions:
        dx = pos[0] - dartboard_center[0]
        dy = pos[1] - dartboard_center[1]
        distance = np.sqrt(dx**2 + dy**2)

        if distance < dartboard_radius * 0.1:
            scores.append(50)  # Bullseye
        elif distance < dartboard_radius * 0.2:
            scores.append(25)  # Outer bullseye
        else:
            # Map to dartboard regions (simplified for this example)
            scores.append(10)  # Example: Assign points for outer regions

    return scores

def main():
    # Initialize camera
    cap = cv2.VideoCapture(0)

    # Start the Flask server in a separate thread
    flask_thread_obj = threading.Thread(target=flask_thread, daemon=True)
    flask_thread_obj.start()

    global scores
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        dartboard = detect_dartboard(frame)
        if dartboard:
            x, y, r = dartboard
            dart_positions = detect_darts(frame, (x, y), r)
            scores = calculate_score(dart_positions, (x, y), r)  # Update the global scores

        cv2.imshow("Dartboard Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    main()
