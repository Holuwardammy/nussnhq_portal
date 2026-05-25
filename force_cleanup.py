import os
import dj_database_url
import psycopg2

print("--- RUNNING CRITICAL PRODUCTION DATABASE CLEANUP ---")

# Pull your live Render database URL directly from the environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    try:
        # Connect directly to PostgreSQL via psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Vaporize the bad row causing the bigint conversion crash
        cursor.execute("DELETE FROM students_student WHERE school_id NOT SIMILAR TO '[0-9]+';")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("SUCCESS: Problematic string rows removed from the student table!")
    except Exception as e:
        print(f"DATABASE CLEANUP FAILED: {e}")
else:
    print("DATABASE_URL not found. Skipping cleanup.")