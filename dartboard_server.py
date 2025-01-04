from flask import Flask, jsonify, request, render_template_string
import sqlite3

app = Flask(__name__)

DB_FILE = "scores.db"

# Global variable to hold the scores
scores = []


# Database Initialization
def initialize_database():
    """Create the database and table if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# Log Scores to Database
def log_scores_to_db(scores):
    """Log the scores to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO scores (score) VALUES (?)", [(score,) for score in scores])
    conn.commit()
    conn.close()


# Retrieve Logged Scores
def get_logged_scores():
    """Retrieve all logged scores from the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, score, timestamp FROM scores")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "score": row[1], "timestamp": row[2]} for row in rows]


@app.route("/")
def index():
    """Render the main page with embedded HTML."""
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dartboard Scores</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 20px; }
            h1 { font-size: 2em; margin-bottom: 20px; }
            table { margin: 0 auto; border-collapse: collapse; width: 50%; }
            th, td { border: 1px solid #ddd; padding: 8px; }
            th { background-color: #f2f2f2; }
            .score { margin-bottom: 10px; }
            input[type="number"] { width: 60px; text-align: center; }
            button { margin-top: 20px; padding: 10px 20px; font-size: 1em; }
        </style>
    </head>
    <body>
        <h1>Dartboard Scores</h1>
        <form id="score-form">
            <div id="scores-section">
                <!-- Scores will be populated here -->
            </div>
            <button type="button" onclick="submitScores()">Update Scores</button>
        </form>
        <h2>Total: <span id="total"></span></h2>

        <h3>Score Log</h3>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Score</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody id="log-section">
                <!-- Score log will be populated here -->
            </tbody>
        </table>

        <script>
            async function loadScores() {
                const response = await fetch("/scores");
                const data = await response.json();
                const scoresSection = document.getElementById("scores-section");
                const logSection = document.getElementById("log-section");
                const totalElement = document.getElementById("total");

                // Populate scores
                scoresSection.innerHTML = "";
                data.scores.forEach((score, index) => {
                    scoresSection.innerHTML += `
                        <div class="score">
                            Dart ${index + 1}: <input type="number" name="score" value="${score}" min="0">
                        </div>
                    `;
                });

                // Populate log
                logSection.innerHTML = "";
                data.log.forEach(log => {
                    logSection.innerHTML += `
                        <tr>
                            <td>${log.id}</td>
                            <td>${log.score}</td>
                            <td>${log.timestamp}</td>
                        </tr>
                    `;
                });

                // Update total
                totalElement.textContent = data.total;
            }

            async function submitScores() {
                const formData = new FormData(document.getElementById("score-form"));
                const scores = Array.from(formData.values()).map(value => parseInt(value, 10));
                await fetch("/scores", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ scores })
                });
                loadScores();
            }

            // Load scores on page load
            loadScores();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)


@app.route("/scores", methods=["GET", "POST"])
def handle_scores():
    """Handle getting and updating scores."""
    global scores
    if request.method == "GET":
        return jsonify(scores=scores, total=sum(scores), log=get_logged_scores())
    elif request.method == "POST":
        data = request.json
        if "scores" in data:
            scores = data["scores"]
            log_scores_to_db(scores)  # Log scores to the database
            return jsonify(success=True, scores=scores, total=sum(scores))
        return jsonify(success=False, message="Invalid data"), 400


@app.route("/log")
def view_log():
    """View logged scores."""
    logs = get_logged_scores()
    return jsonify(logs=logs)


if __name__ == "__main__":
    # Initialize the database when the server starts
    initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=False)
