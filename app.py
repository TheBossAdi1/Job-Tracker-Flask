from flask import Flask, render_template, request, redirect, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import sqlite3

app = Flask(__name__)
app.secret_key = "something"

def error(message, code=400):
    return render_template(
        "error.html",
        message=message,
        code=code
    ), code

def get_db():
    conn = sqlite3.connect("applications.db")
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Basic validation
        if not username or len(username) < 4:
            return error("Username must be at least 4 characters", 400)

        if not password or len(password) < 6:
            return error("Password must be at least 6 characters", 400)

        if password != confirmation:
            return error("Passwords do not match", 400)

        # Insert user into database
        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )

            conn.commit()

            # Get new user's id
            user_id = cursor.lastrowid

            conn.close()

        except sqlite3.IntegrityError:
            return error("Username already exists", 400)

        # Log user in
        session["user_id"] = user_id
        return redirect("/")

    # GET
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Basic validation
        if not username or not password:
            return error("Must provide username and password", 400)

        # Query database for user
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )

        user = cursor.fetchone()
        conn.close()

        if user is None or not check_password_hash(user["hash"], password):
            return error("Invalid username or password", 400)

        # Log user in
        session["user_id"] = user["id"]
        return redirect("/")

    # GET
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM applications WHERE user_id = ?", (user_id,))
    applications = cursor.fetchall()
    conn.close()
    return render_template("index.html", applications=applications)

@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        action = request.form.get("action")

        company_name = request.form.get("company_name")
        position = request.form.get("position")
        job_type = request.form.get("job_type")
        job_description = request.form.get("job_description")
        status = request.form.get("status")

        app_id = request.form.get("app_id")

        # ADD new application
        if action == "add":
            cursor.execute(
                """
                INSERT INTO applications
                (user_id, company_name, position, job_type, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, company_name, position, job_type, status)
            )

        # UPDATE existing application
        elif action == "update":
            status = request.form.get("status")

            cursor.execute(
                "UPDATE applications SET status = ? WHERE id = ? AND user_id = ?",
                (status, app_id, user_id)
            )


        # DELETE application
        elif action == "delete":
            cursor.execute(
                "DELETE FROM applications WHERE id = ? AND user_id = ?",
                (app_id, user_id)
            )

        conn.commit()
        conn.close()
        return redirect("/")

    # GET = load applications for this user
    cursor.execute(
        "SELECT * FROM applications WHERE user_id = ?",
        (user_id,)
    )
    applications = cursor.fetchall()
    conn.close()

    return render_template("edit.html", applications=applications)

@app.route("/charts")
@login_required
def charts():
    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()

    # Status data
    cursor.execute(
        "SELECT status, COUNT(*) AS count FROM applications WHERE user_id = ? GROUP BY status",
        (user_id,)
    )
    status_rows = cursor.fetchall()
    status_data = [
        {"status": row["status"], "count": row["count"]}
        for row in status_rows
    ]

    # Job type data
    cursor.execute(
        "SELECT job_type, COUNT(*) AS count FROM applications WHERE user_id = ? GROUP BY job_type",
        (user_id,)
    )
    job_type_rows = cursor.fetchall()
    job_type_data = [
        {"job_type": row["job_type"], "count": row["count"]}
        for row in job_type_rows
    ]

    conn.close()

    return render_template(
        "charts.html",
        status_data=status_data,
        job_type_data=job_type_data
    )




if __name__ == "__main__":
    app.run(debug=True)
    