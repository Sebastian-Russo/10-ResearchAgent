from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

from src.research_agent import ResearchAgent
from src.config         import REPORTS_DIR

app    = Flask(__name__, static_folder="static")
CORS(app)
agent  = ResearchAgent()


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/research", methods=["POST"])
def research():
    data  = request.get_json()
    topic = data.get("topic", "").strip()
    depth = data.get("depth", "fast").strip()

    if not topic:
        return jsonify({"error": "No topic provided"}), 400

    if depth not in ["fast", "deep"]:
        depth = "fast"

    result = agent.research(topic, depth)
    return jsonify(result)


@app.route("/reports", methods=["GET"])
def list_reports():
    """Return a list of all saved reports."""
    if not os.path.exists(REPORTS_DIR):
        return jsonify([])

    files = sorted(
        [f for f in os.listdir(REPORTS_DIR) if f.endswith(".md")],
        reverse=True   # newest first
    )
    return jsonify(files)


@app.route("/reports/<filename>", methods=["GET"])
def get_report(filename):
    """Return the contents of a specific saved report."""
    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "Report not found"}), 404

    with open(filepath, "r") as f:
        return jsonify({"content": f.read(), "filename": filename})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
