import sqlite3

conn = sqlite3.connect("applications.db")
cursor = conn.cursor()

# Users table
cursor.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL
);
""")

# Applications table
cursor.execute("""
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    company_name TEXT NOT NULL,
    position TEXT,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    date_applied TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
    );
""")

# Indexes for performance
cursor.execute("CREATE INDEX idx_applications_user ON applications(user_id);")
cursor.execute("CREATE INDEX idx_applications_status ON applications(status);")
cursor.execute("CREATE INDEX idx_applications_job_type ON applications(job_type);")

conn.commit()
conn.close()
