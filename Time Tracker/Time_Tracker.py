import random
import sqlite3
from datetime import datetime, date, timedelta

letters = list('qwertyuiopasdfghjklzxcvbnm')
letter_or_number = ['letter', 'number']
current_date = date.today()
user_phrase_time_date = {}
current_user = None
end_time = None


def init_db():
    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            phrase TEXT UNIQUE NOT NULL,
            start_time TEXT,
            end_time TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()


def creating_phrase():
    """Generate a random 12-character alphanumeric phrase."""
    phrase = ''
    while len(phrase) < 12:
        if random.choice(letter_or_number) == 'letter':
            phrase += random.choice(letters)
        else:
            phrase += str(random.randint(0, 9))
    return phrase


def login_user(email):
    """Store current user globally (called when login succeeds)."""
    global current_user
    current_user = email.strip()
    print(f"Logged in as {current_user}")


def start_tracker():
    """Start tracking time for the current user."""
    global user_phrase_time_date, end_time, current_user

    if not current_user:
        print("No user logged in.")
        return None

    phrase = creating_phrase()
    start_time = datetime.now()
    user_phrase_time_date[phrase] = [current_user, start_time, None, current_date]

    print(f"Tracker started for {current_user} at {start_time.strftime('%H:%M:%S')}")
    return phrase


def stop_tracker(phrase):
    """Stop tracking and save record to database."""
    global user_phrase_time_date

    if phrase not in user_phrase_time_date:
        print("Invalid phrase. No tracker found.")
        return False

    end_time = datetime.now()
    user_phrase_time_date[phrase][2] = end_time

    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_tracker (user_email, phrase, start_time, end_time, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        user_phrase_time_date[phrase][0],
        phrase,
        user_phrase_time_date[phrase][1].strftime("%H:%M:%S"),
        user_phrase_time_date[phrase][2].strftime("%H:%M:%S"),
        user_phrase_time_date[phrase][3].strftime("%Y-%m-%d")
    ))
    conn.commit()
    conn.close()

    print(f"Tracker stopped for {current_user} at {end_time.strftime('%H:%M:%S')}")
    return True


def daily_time_calculator(from_date: str = None, to_date: str = None):
    """
    Calculate total tracked time for the current user within an optional date range.
    
    Parameters:
        from_date (str): Start date in 'YYYY-MM-DD' format.
        to_date (str): End date in 'YYYY-MM-DD' format.
    """
    global current_user

    if not current_user:
        print("\nYou must log in first.")
        return timedelta(0)

    # Validate and parse the date range
    if from_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
        except ValueError:
            print("FROM date must be in YYYY-MM-DD format.")
            return timedelta(0)
    else:
        from_dt = date.min

    if to_date:
        try:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
        except ValueError:
            print("TO date must be in YYYY-MM-DD format.")
            return timedelta(0)
    else:
        to_dt = date.max

    conn = sqlite3.connect("tracker.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT start_time, end_time, date FROM user_tracker
        WHERE user_email = ?
    ''', (current_user,))
    records = cursor.fetchall()
    conn.close()

    if not records:
        print("No records found for this user.")
        return timedelta(0)

    total_seconds = 0
    for start_str, end_str, work_date_str in records:
        work_date = datetime.strptime(work_date_str, "%Y-%m-%d").date()
        if not (from_dt <= work_date <= to_dt):
            continue  # skip records outside the range

        start_dt = datetime.strptime(f"{work_date_str} {start_str}", "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(f"{work_date_str} {end_str}", "%Y-%m-%d %H:%M:%S")
        delta = end_dt - start_dt
        total_seconds += delta.total_seconds()

    total_time = timedelta(seconds=total_seconds)
    print(f"Total time worked from {from_dt} to {to_dt}: {total_time}")
    return total_time
