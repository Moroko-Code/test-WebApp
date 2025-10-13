import os
import pyodbc
from flask import Flask, render_template_

# --- App Initialization ---
app = Flask(__name__)

# --- Configuration (Read from Environment) ---
# For local testing, ensure DB_CONNECTION_STRING is set in the terminal
# or loaded via python-dotenv if you use it.
DB_CONNECTION_STRING = os.environ.get("DB_CONNECTION_STRING")

# Basic check to ensure the connection string is available
if not DB_CONNECTION_STRING:
    print("WARNING: DB_CONNECTION_STRING environment variable not set. Application will fail on database access.")

# --- Database and Data Setup ---
TABLE_NAME = "items"
INSERT_SQL = f"INSERT INTO {TABLE_NAME} (name, price, description) VALUES (?, ?, ?)"
SELECT_SQL = f"SELECT id, name, price, description FROM {TABLE_NAME}" # Added SELECT query

dummy_data = [
    ("Laptop Pro", 1999.99, "High-performance business laptop."),
    ("Wireless Mouse", 35.50, "Ergonomic 6-button mouse."),
    ("Mechanical Keyboard", 120.00, "Full-size, backlit mechanical keyboard."),
    ("4K Monitor 27\"", 450.00, "27-inch monitor with 4K resolution."),
    ("HD Webcam", 62.99, "1080p webcam with auto-focus."),
]

# --- Database Functions ---
def execute_db_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """General function to handle all DB operations (Connect, Query, Close)."""
    conn = None
    results = None
    
    if not DB_CONNECTION_STRING:
        return results

    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if commit:
            conn.commit()
        
        if fetch_one:
            results = cursor.fetchone()
        elif fetch_all:
            results = cursor.fetchall()
            
    except pyodbc.Error as e:
        print(f"❌ Database Error: {e}")
        if conn and commit:
            conn.rollback()
            
    finally:
        if conn:
            conn.close()
            
    return results

def insert_dummy_data_if_empty():
    """Checks if the table is empty and inserts data if it is."""
    # Check if table exists and has data (e.g., SELECT TOP 1)
    check_query = f"SELECT COUNT(*) FROM {TABLE_NAME}"
    count = execute_db_query(check_query, fetch_one=True)
    
    # If count[0] is None (table might not exist yet) or 0, insert data
    if count is None or count[0] == 0:
        print(f"INFO: Table '{TABLE_NAME}' is empty or not found. Inserting dummy data...")
        
        try:
            # Re-establish connection for executemany, or loop through data
            conn = pyodbc.connect(DB_CONNECTION_STRING)
            cursor = conn.cursor()
            cursor.executemany(INSERT_SQL, dummy_data)
            conn.commit()
            conn.close()
            print(f"✅ Successfully inserted {len(dummy_data)} rows.")
        except pyodbc.Error as e:
            # Handle error where table might not exist at all (initial run)
            print(f"❌ Insertion failed. Ensure table '{TABLE_NAME}' exists with (name, price, description) columns. Error: {e}")
            pass # Continue to allow the SELECT query to fail gracefully if the table is the issue.
            
    else:
        print(f"INFO: Table '{TABLE_NAME}' already contains {count[0]} records. Skipping insertion.")

# --- Flask Route ---
@app.route("/")
def index():
    # 1. Ensure data is available (for first run)
    insert_dummy_data_if_empty()
    
    # 2. Fetch all data for display
    items_data = execute_db_query(SELECT_SQL, fetch_all=True)

    if items_data is None:
        # Connection failed or table doesn't exist.
        return "<h1>Database Connection Failed</h1><p>Check the DB_CONNECTION_STRING and ensure the database/table is accessible.</p>", 500
    
    # 3. Render the page with the fetched data
    return render_template("index.html", items=items_data)

# --- Run Application ---
if __name__ == "__main__":   
    app.run(debug=True)