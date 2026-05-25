import os
import dj_database_url
import psycopg2

print("--- RUNNING CRITICAL PRODUCTION DATABASE CLEANUP ---")

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # CHANGED: 'school_id' is changed to 'school' to match your current production column name
        cursor.execute("DELETE FROM students_student WHERE school NOT SIMILAR TO '[0-9]+';")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("SUCCESS: Problematic string rows removed from the student table!")
    except Exception as e:
        print(f"DATABASE CLEANUP FAILED: {e}")
else:
    print("DATABASE_URL not found. Skipping cleanup.")