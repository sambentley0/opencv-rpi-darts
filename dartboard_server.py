from flask import Flask, jsonify, render_template
import threading
import time

app = Flask(__name__)

# Global variable to hold the scores
scores = []

@app.route("/")
def index():
    """Render the HTML page."""
    return render_template("index.html")

@app.route("/scores")
def get_scores():
    """API endpoint to get the current scores."""
    return jsonify(scores=scores, total=sum(scores))

def flask_thread():
    """Run the Flask server in a separate thread."""
    app.run(host="0.0.0.0", port=5000, debug=False)

# HTML Template (index.html)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dartboard Scores</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        h1 { font-size: 2.5em; }
        .score { font-size: 1.5em; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Dartboard Scores</h1>
    <div id="scores">
        Loading scores...
    </div>
    <script>
        async function fetchScores() {
            const response = await fetch("/scores");
            const data = await response.json();
            const scoresDiv = document.getElementById("scores");
            let scoresHtml = data.scores.map((score, index) => `Dart ${index + 1}: ${score}`).join("<br>");
            scoresHtml += `<br><strong>Total: ${data.total}</strong>`;
            scoresDiv.innerHTML = scoresHtml;
        }
        setInterval(fetchScores, 1000); // Refresh scores every second
        fetchScores();
    </script>
</body>
</html>
"""

# Save the HTML template to a file
with open("templates/index.html", "w") as f:
    f.write(HTML_TEMPLATE)
