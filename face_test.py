import dlib
import face_recognition
import cv2
import numpy as np
import os
import sys

print("=== Face Recognition Test ===")
print(f"Python version: {sys.version}")
print(f"dlib version: {dlib.__version__}")
print(f"face_recognition version: {face_recognition.__version__}")
print(f"OpenCV version: {cv2.__version__}")
print(f"NumPy version: {np.__version__}")

# Test image path (create a simple image if none exists)
test_image_path = "test_face.jpg.jpg"
if not os.path.exists(test_image_path):
    # Create a blank test image
    cv2.imwrite(test_image_path, np.zeros((500, 500, 3), dtype=np.uint8))
    print(f"\nCreated test image at {test_image_path}")
    print("Please replace it with a real face image for proper testing")
else:
    print(f"\nUsing existing test image: {test_image_path}")

try:
    # Load the image
    image = face_recognition.load_image_file(test_image_path)
    print("\nImage loaded successfully!")
    print(f"Image shape: {image.shape}")

    # Face detection test
    face_locations = face_recognition.face_locations(image)
    print(f"\nFound {len(face_locations)} face(s) in the image")

    if len(face_locations) > 0:
        print("\nFirst face location (top, right, bottom, left):")
        print(face_locations[0])
    else:
        print("\nNo faces detected - try with a clearer face image")

    # Encoding test
    if len(face_locations) > 0:
        encodings = face_recognition.face_encodings(image, face_locations)
        print(f"\nGenerated {len(encodings)} face encoding(s)")
        print(f"Each encoding has {len(encodings[0])} dimensions")

except Exception as e:
    print("\nERROR:", str(e))
    print("\nPlease check:")
    print("1. The test image exists and is readable")
    print("2. All packages are properly installed")
    print("3. Your Python environment is correct")