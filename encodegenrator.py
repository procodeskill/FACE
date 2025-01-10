

import cv2
import face_recognition
import os
import uuid
import json
from dotenv import load_dotenv
from supabase import create_client
import numpy as np

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL or API key is missing in .env file!")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Function to find encodings for images
def find_encodings(images_list):
    encode_list = []
    for img in images_list:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img)  # Get all encodings in the image
        if encodings:  # Ensure at least one face was detected
            encode_list.append(encodings[0])
        else:
            print("Warning: No face detected in an image.")
            encode_list.append(None)  # Append None if no face is found
    return encode_list

# Upload an image to Supabase storage
def upload_image_to_supabase(image_path, student_name):
    # Generate a unique filename using UUID
    unique_filename = str(uuid.uuid4()) + os.path.splitext(image_path)[1]
    file_path = f"student_images/{unique_filename}"  # Path in Supabase storage

    # Upload the image
    with open(image_path, "rb") as file:
        response = supabase.storage.from_("student_images").upload(file_path, file)

    # Check if the upload was successful
    if hasattr(response, "path") and response.path:
        correct_path = response.path.replace("student_images/student_images/", "student_images/")
        print(f"Image uploaded successfully: {correct_path}")
        return correct_path
    else:
        print(f"Unexpected response during upload: {response}")
        return None

# Insert a single student into the database
def insert_student_with_image(student_name, student_image, student_face_encoding):
    # Convert face encoding to list for JSON serialization
    if student_face_encoding is None:
        print(f"Skipping {student_name} due to no face encoding.")
        return

    # Upload the image to Supabase storage
    image_url = upload_image_to_supabase(student_image, student_name)
    if image_url:
        # Create the student data
        student_data = {
            "name": student_name,
            "attendance_count": 0,
            "face_encoding": student_face_encoding.tolist(),
            "last_attendance": None,
            "image_url": image_url
        }

        # Insert into Supabase Database
        response = supabase.table("students").insert(student_data).execute()
        if response.data:
            print(f"Inserted student: {response.data}")
        else:
            print(f"Error inserting student into database: {response.error}")
    else:
        print("Failed to upload image. Student data not inserted.")

# Main script to process images and students
folderpath = 'Images'  # Folder containing student images

path_list = os.listdir(folderpath)
img_list = []
student_ids = []

# Load images and student IDs
for path in path_list:
    img_path = os.path.join(folderpath, path)
    img = cv2.imread(img_path)
    if img is not None:
        img_list.append(img)
        student_ids.append(os.path.splitext(path)[0])  # Use filename (without extension) as student ID

# Find encodings for the images
print("Encoding images...")
encode_list_known = find_encodings(img_list)

# Prepare and insert student data into Supabase
for student_name, student_image_path, student_encoding in zip(student_ids, path_list, encode_list_known):
    if student_encoding is None:
        print(f"Skipping {student_name}: No face encoding.")
        continue

    image_path = os.path.join(folderpath, student_image_path)  # Full path to image
    insert_student_with_image(student_name, image_path, student_encoding)

print("Processing complete!")
