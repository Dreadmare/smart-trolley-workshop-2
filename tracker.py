import cv2
from ultralytics import YOLO

# 1. Load the lightweight YOLOv8n model
# It will automatically download the 'yolov8n.pt' weights file on the first run
model = YOLO("yolov8n.pt")

# 2. Initialize the webcam (index 0 is typically the built-in laptop camera)
cap = cv2.VideoCapture(0)

# Set resolution to 640x480 to match the 220 and 420 X_center thresholds
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Starting camera... Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame. Exiting...")
        break

    # 3. Run YOLOv8 inference
    # classes=[0] filters for 'person' only; conf=0.50 enforces the confidence threshold
    results = model(frame, classes=[0], conf=0.50)

    # 4. Process the detections
    for result in results:
        for box in result.boxes:
            # Extract coordinates and confidence
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])

            # Calculate horizontal centroid (X_center) and bounding box area (A_box)
            x_center = int((x1 + x2) / 2)
            y_center = int((y1 + y2) / 2)
            a_box = (x2 - x1) * (y2 - y1)

            # Determine position based on X_center
            if x_center < 220:
                position = "Left"
            elif x_center <= 420:
                position = "Center"
            else:
                position = "Right"

            # Report data to the console
            print(f"Person Detected -> Zone: {position} | X_center: {x_center} | Area: {a_box} | Conf: {conf:.2f}")

            # Draw bounding box on the frame
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw the centroid dot
            cv2.circle(frame, (x_center, y_center), 5, (0, 0, 255), -1)

            # Overlay status text
            label = f"{position} | Conf: {conf:.2f} | Area: {a_box}"
            cv2.putText(frame, label, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Display the live video feed
    cv2.imshow("Person Detection Tracking", frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up resources
cap.release()
cv2.destroyAllWindows()
