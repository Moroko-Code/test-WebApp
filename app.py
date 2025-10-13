import os
import pyodbc
from flask import Flask, render_template

# --- App Initialization ---
app = Flask(__name__)

# --- Configuration (Read from Environment) ---
DB_CONNECTION_STRING = os.environ.get("DB_CONNECTION_STRING")

if not DB_CONNECTION_STRING:
    print("⚠️ WARNING: DB_CONNECTION_STRING environment variable not set. "
          "Application will fail on database access.")

# --- Database Configuration ---
TABLE_NAME = "items"
INSERT_SQL = f"INSERT INTO {TABLE_NAME} (name, price, description) VALUES (?, ?, ?)"
SELECT_SQL = f"SELECT id, name, price, description FROM {TABLE_NAME}"

dummy_data = [
    ("Laptop Pro", 1999.99, "High-performance business laptop."),
    ("Wireless Mouse", 35.50, "Ergonomic 6-button mouse."),
    ("Mechanical Keyboard", 120.00, "Full-size, backlit mechanical keyboard."),
    ("4K Monitor 27\"", 450.00, "27-inch monitor with 4K resolution."),
    ("HD Webcam", 62.99, "1080p webcam with auto-focus."),
]

# --- Database Utility Function ---
def execute_db_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """General-purpose function for database operations."""
    if not DB_CONNECTION_STRING:
        print("❌ No DB connection string configured.")
        return None

    conn = None
    results = None

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
        print(f"❌ Database error: {e}")
        if conn and commit:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    return results


def insert_dummy_data_if_empty():
    """Checks if the items table is empty and inserts dummy data if needed."""
    if not DB_CONNECTION_STRING:
        print("⚠️ Skipping data insertion — no DB connection string configured.")
        return

    try:
        count = execute_db_query(f"SELECT COUNT(*) FROM {TABLE_NAME}", fetch_one=True)
    except Exception as e:
        print(f"⚠️ Could not query table '{TABLE_NAME}': {e}")
        count = None

    # Insert if table is empty or not accessible
    if count is None or count[0] == 0:
        print(f"ℹ️ Table '{TABLE_NAME}' is empty or missing. Inserting dummy data...")
        try:
            conn = pyodbc.connect(DB_CONNECTION_STRING)
            cursor = conn.cursor()
            cursor.executemany(INSERT_SQL, dummy_data)
            conn.commit()
            conn.close()
            print(f"✅ Successfully inserted {len(dummy_data)} records.")
        except pyodbc.Error as e:
            print(f"❌ Insert failed — table '{TABLE_NAME}' may not exist. Error: {e}")
    else:
        print(f"ℹ️ Table '{TABLE_NAME}' already contains {count[0]} records. Skipping insertion.")


# --- Flask Routes ---
@app.route("/")
def index():
    insert_dummy_data_if_empty()
    items_data = execute_db_query(SELECT_SQL, fetch_all=True)

    if items_data is None:
        return (
            "<h1>Database Connection Failed</h1>"
            "<p>Check your DB_CONNECTION_STRING and ensure the database/table is accessible.</p>",
            500,
        )

    return render_template("index.html", items=items_data)


# --- Main Entry Point ---
if __name__ == "__main__":
    print("🚀 Starting Flask app...")
    app.run(debug=True, host="0.0.0.0", port=5000)
