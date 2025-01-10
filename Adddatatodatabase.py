
from dotenv import load_dotenv
import os
from supabase import create_client
from encodegenrator import encode_list_known  # Import from encodinggenerator.py

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def insert_students(students_data):
    # Log the data for debugging
    print("Inserting data:", students_data)
    
    # Use UPSERT to avoid duplicate rows
    response = supabase.table("students").upsert(students_data).execute()
    
    # Log the response
    print("Response from Supabase:", response)
    return response.data

# Example usage
if __name__ == "__main__":
    # Convert the ndarray face encodings into lists
    students_data = [
        {
            "id": "321654",
            "name": "Mustad",
            "attendance_count": 0,
            "last_attendance": "2025-01-03T21:15:52",
            "major": "Mathematics",
            "standing": "11th",
            "face_encoding": encode_list_known[0].tolist(),  # Use unique encoding
            "year": 2025,
            "starting_year": 2023
        },
        {
            "id": "963852",
            "name": "Elon musk",
            "attendance_count": 0,
            "last_attendance": "2025-01-03T21:15:52",
            "major": "English",
            "standing": "12th",
            "face_encoding": encode_list_known[1].tolist(),  # Ensure this is a list or JSON, not a string
            "year": 2025,
            "starting_year": 2021
        },
        {
            "id": "11111",
            "name": "Ashok",
            "attendance_count": 0,
            "last_attendance": "2025-01-03T21:15:52",
            "major": "English",
            "standing": "10th",
            "face_encoding": encode_list_known[2].tolist(),  # Ensure this is a list or JSON, not a string
            "year": 2025,
            "starting_year": 2021
        },
    ]

    # Insert the student data
    response = insert_students(students_data)
    print("Inserted students:", response)
