
import cv2
import os
import numpy as np
import face_recognition
import pickle
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase
url = "https://lxushrynihxftbmxnjcl.supabase.co"  # Replace with your Supabase URL
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4dXNocnluaWh4ZnRibXhuamNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzU4NDE0MjUsImV4cCI6MjA1MTQxNzQyNX0.3Y142b6WRkLXyZQInaExnXNfUkVOvQLwkuw3-A4VHzw"  # Replace with your API key
supabase: Client = create_client(url, key)

# Initialize the webcam
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Set width
cap.set(4, 480)  # Set height

# Load the background image
imgbackground = cv2.imread('Resources/background.png')

# Load mode images
foldermodepath = 'Resources/Modes'
modepathlist = os.listdir(foldermodepath)
imgmodelist = [cv2.imread(os.path.join(foldermodepath, path)) for path in modepathlist]

# Load the encoding file
with open('Encodefile.p', 'rb') as file:
    Encodelistknownwithids = pickle.load(file)
Encodelistknown, studentids = Encodelistknownwithids

# Debug loaded data
print(f"Loaded student IDs: {studentids}")

# Variables
modetype = 0
counter = 0
id = -1
studentinfo = None
bucket = supabase.storage.from_("student_images")
imgstudents = []
default_image_path = "Resources/default_student_image.png"  # Path to a default image

while True:
    success, img = cap.read()
    if not success:
        break

    # Resize and convert the image to RGB
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Find face locations and encodings
    facecurframe = face_recognition.face_locations(imgS)
    encodecurframes = face_recognition.face_encodings(imgS, facecurframe)

    # Update the background image
    imgbackground[162:162 + 480, 55:55 + 640] = img
    imgbackground[44:44 + 633, 808:808 + 414] = imgmodelist[modetype]

    for encodeface, faceloc in zip(encodecurframes, facecurframe):
        matches = face_recognition.compare_faces(Encodelistknown, encodeface)
        facedis = face_recognition.face_distance(Encodelistknown, encodeface)

        # Debug face matching
        print(f"Face Distances: {facedis}")
        print(f"Match Results: {matches}")

        if matches:
            matchindex = np.argmin(facedis)
            if matches[matchindex]:
                student_id = studentids[matchindex]

                # Fetch student info from the database
                response = supabase.table("students").select("*").eq("id", student_id).execute()
                print(f"Database Query Response: {response.data}")  # Debug response

                if not response.data:
                    print(f"No record found for student ID: {student_id}")  # Handle case where no data is returned
                    continue

                studentinfo = response.data[0]  # Assuming 'id' is the primary key
                print("Fetched Student Info:", studentinfo)  # Debug student info

                # Update attendance: Increment count and update last attendance
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Format time as you prefer
                update_response = supabase.table("students").update({
                    "attendance_count": studentinfo["attendance_count"] + 1,
                    "last_attendance": current_time
                }).eq("id", student_id).execute()
                print(f"Attendance Update Response: {update_response}")

                # Set the counter and modetype as before
                if counter == 0:
                    counter = 1
                    modetype = 1

        if counter != 0:
            if counter == 1:
                # Fetch the student info from the database again
                studentinfo_response = supabase.table("students").select("*").eq("id", student_id).execute()
                studentinfo = studentinfo_response.data[0] if studentinfo_response.data else None

                # Attempt to fetch the student's image from storage
                try:
                    # Attempt to download the image for the student
                    imgstudents = None
                    blob = bucket.download(f"student_images/elon.png")
                    if blob:
                        array = np.frombuffer(blob, np.uint8)
                        imgstudents = cv2.imdecode(array, cv2.IMREAD_COLOR)
                    else:
                        print(f"Image for student ID {student_id} not found in storage.")
                        imgstudents = cv2.imread(default_image_path)  # Use default image
                except Exception as e:
                    print(f"Error downloading the image for ID {student_id}: {e}")
                    imgstudents = cv2.imread(default_image_path)  # Use default image

            if studentinfo:
                print(studentinfo)
                cv2.putText(imgbackground, str(studentinfo['attendance_count']), (861, 125),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                cv2.putText(imgbackground, str(studentinfo['major']), (1006, 550),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgbackground, str(student_id), (1006, 493),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgbackground, str(studentinfo['standing']), (910, 625),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(imgbackground, str(studentinfo['year']), (1025, 625),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(imgbackground, str(studentinfo['starting_year']), (1125, 625),
                            cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                (w, h), _ = cv2.getTextSize(studentinfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                offset = (414 - w) // 2
                cv2.putText(imgbackground, str(studentinfo['name']), (808 + offset, 445),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                # Ensure imgstudents is not None before assigning
                if imgstudents is not None:
                    imgbackground[175:175 + 216, 909:909 + 216] = imgstudents
                else:
                    print(f"Warning: Image for student ID {student_id} is not available.")

            counter += 1

    # Display the image
    cv2.imshow("Webcam", imgbackground)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
