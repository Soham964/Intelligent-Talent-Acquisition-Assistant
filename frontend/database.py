import sqlite3
from pathlib import Path
import datetime

class InterviewDatabase:
    def __init__(self):
        self.db_path = Path(__file__).parent / 'interview_slots.db'
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interview_slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_name TEXT NOT NULL,
                    interview_date TEXT NOT NULL,
                    interview_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def schedule_interview(self, candidate_name, interview_date, interview_time, status='scheduled'):
        try:
            # Input validation
            if not all([candidate_name, interview_date, interview_time]):
                error_msg = "Error: All fields (candidate_name, interview_date, interview_time) are required"
                print(error_msg)
                return False, error_msg

            # Validate date format
            try:
                datetime.datetime.strptime(interview_date, '%Y-%m-%d')
            except ValueError:
                error_msg = f"Error: Invalid date format for {interview_date}. Expected format: YYYY-MM-DD"
                print(error_msg)
                return False, error_msg

            # Validate and standardize time format
            try:
                # Try 24-hour format first
                time_obj = datetime.datetime.strptime(interview_time, '%H:%M')
                # Standardize to 24-hour format
                interview_time = time_obj.strftime('%H:%M')
            except ValueError:
                try:
                    # Try 12-hour format and convert to 24-hour
                    time_obj = datetime.datetime.strptime(interview_time, '%I:%M %p')
                    # Convert to 24-hour format
                    interview_time = time_obj.strftime('%H:%M')
                except ValueError:
                    error_msg = f"Error: Invalid time format for {interview_time}. Expected format: HH:MM (24-hour) or HH:MM AM/PM (12-hour)"
                    print(error_msg)
                    return False, error_msg

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if the slot is already booked
                cursor.execute('''
                    SELECT candidate_name FROM interview_slots 
                    WHERE interview_date = ? AND interview_time = ? AND status = 'scheduled'
                ''', (interview_date, interview_time))
                
                existing_booking = cursor.fetchone()
                if existing_booking:
                    error_msg = f"Error: Time slot {interview_date} {interview_time} is already booked by {existing_booking[0]}"
                    print(error_msg)
                    return False, error_msg

                # Check if candidate already has an interview scheduled
                cursor.execute('''
                    SELECT interview_date, interview_time FROM interview_slots 
                    WHERE candidate_name = ? AND status = 'scheduled'
                ''', (candidate_name,))
                
                existing_interview = cursor.fetchone()
                if existing_interview:
                    error_msg = f"Error: {candidate_name} already has an interview scheduled for {existing_interview[0]} at {existing_interview[1]}"
                    print(error_msg)
                    return False, error_msg

                try:
                    cursor.execute('''
                        INSERT INTO interview_slots (candidate_name, interview_date, interview_time, status)
                        VALUES (?, ?, ?, ?)
                    ''', (candidate_name, interview_date, interview_time, status))
                    conn.commit()
                    success_msg = f"Success: Interview scheduled for {candidate_name} on {interview_date} at {interview_time}"
                    print(success_msg)
                    return True, success_msg
                except sqlite3.Error as e:
                    error_msg = f"Database error during insertion: {e}"
                    print(error_msg)
                    return False, error_msg

        except sqlite3.Error as e:
            error_msg = f"Database error: {e}"
            print(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(error_msg)
            return False, error_msg

    def get_all_scheduled_interviews(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM interview_slots 
                WHERE status = "scheduled" 
                ORDER BY interview_date, interview_time
            ''')
            columns = [description[0] for description in cursor.description]
            interviews = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return interviews

    def get_booked_slots(self):
        interviews = self.get_all_scheduled_interviews()
        booked_slots = {}
        for interview in interviews:
            slot_key = f"{interview['interview_date']} {interview['interview_time']}"
            booked_slots[slot_key] = {
                'candidate_name': interview['candidate_name'],
                'status': interview['status']
            }
        return booked_slots

    def clear_all_interviews(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM interview_slots')
                conn.commit()
                return True
        except sqlite3.Error as e:
            error_msg = f"Database error: {e}"
            print(error_msg)
            return False, error_msg
        except Exception as e:
            print(f"Error: {e}")
            return False

    def delete_interview(self, candidate_name, interview_date, interview_time):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # First check if the interview exists and get its status
                cursor.execute('''
                    SELECT id, status 
                    FROM interview_slots 
                    WHERE candidate_name = ? 
                    AND interview_date = ? 
                    AND interview_time = ?
                ''', (candidate_name, interview_date, interview_time))
                result = cursor.fetchone()
                
                if not result:
                    print(f"No interview found for {candidate_name} at {interview_date} {interview_time}. Please verify the details.")
                    return False
                
                interview_id, current_status = result
                
                if current_status != 'scheduled':
                    print(f"Cannot delete interview - current status is '{current_status}'. Only scheduled interviews can be deleted.")
                    return False
                
                # If we reach here, the interview exists and is scheduled, so delete it
                cursor.execute('''
                    DELETE FROM interview_slots
                    WHERE id = ? AND status = 'scheduled'
                ''', (interview_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    print(f"Successfully deleted scheduled interview for {candidate_name}")
                    return True
                else:
                    print(f"Unexpected error: Interview status may have changed during deletion")
                    return False
                    
        except sqlite3.Error as e:
            error_msg = f"Database error: {e}"
            print(error_msg)
            return False, error_msg
        except Exception as e:
            print(f"Error: {e}")
            return False