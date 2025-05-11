import face_recognition
import cv2

def verify_face(image_path):
    # Load the image
    known_image = cv2.imread(image_path)

    # Check if image loaded properly
    if known_image is None:
        raise ValueError("Image not found or unreadable! Check the path or file format.")

    print("Original image shape:", known_image.shape)

    # If grayscale, convert to RGB
    if len(known_image.shape) == 2:
        known_image = cv2.cvtColor(known_image, cv2.COLOR_GRAY2RGB)
    else:
        # Convert BGR to RGB
        known_image = cv2.cvtColor(known_image, cv2.COLOR_BGR2RGB)

    print("Converted image shape:", known_image.shape)

    # Try getting face encodings
    encodings = face_recognition.face_encodings(known_image)
    if not encodings:
        raise ValueError("No face found in the image.")

    return encodings[0]
