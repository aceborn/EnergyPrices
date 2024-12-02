from flask import Flask, send_file, make_response
from flask_compress import Compress
import os
import threading
import schedule
import time
from main import main

app = Flask(__name__)
Compress(app)

GRAPH_FILE = "day_ahead_prices_barchart.html"

# Define a root route
@app.route('/')
def home():
    return "Welcome to the Energy Prices App! Visit /graph to see the graph."


# Define the /graph route
@app.route('/graph')
def serve_graph():
    """Serve the latest interactive graph as an HTML page."""
    if os.path.exists(GRAPH_FILE):
        response = make_response(send_file(GRAPH_FILE, mimetype='text/html'))
        response.headers['Cache-Control'] = 'public, max-age=21600'  # Cache for 6 hours
        return response
    else:
        return "Graph not available", 404

# Function to run the Flask app
def run_flask():
    app.run(host='0.0.0.0', port=5000)

# Function to run the scheduler
def run_scheduler():
    print("Starting 6-hourly chart update scheduler...")
    main()  # Run the chart generation immediately on startup
    schedule.every(6).hours.do(main)  # Schedule the main() function to run every 6 hours
    while True:
        schedule.run_pending()
        time.sleep(1)  # Avoid CPU overuse

if __name__ == "__main__":
    # Start both the Flask server and the scheduler using threading
    flask_thread = threading.Thread(target=run_flask)
    scheduler_thread = threading.Thread(target=run_scheduler)

    flask_thread.start()  # Start the Flask server in a separate thread
    scheduler_thread.start()  # Start the scheduler in another thread

    # Wait for threads to finish (they won't in this case)
    flask_thread.join()
    scheduler_thread.join()