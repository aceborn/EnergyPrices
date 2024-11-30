from flask import Flask, send_file
import os

app = Flask(__name__)

GRAPH_FILE = "day_ahead_prices_barchart.html"

@app.route('/graph')
def serve_graph():
    """Serve the latest interactive graph as an HTML page."""
    if os.path.exists(GRAPH_FILE):
        return send_file(GRAPH_FILE, mimetype='text/html')
    else:
        return "Graph not available", 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)