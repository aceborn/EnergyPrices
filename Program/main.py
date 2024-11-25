from entsoe import EntsoePandasClient
from dotenv import load_dotenv
import time
import schedule
import os
import pandas as pd
import plotly.graph_objects as go

def main(): 
    # Load .env file
    load_dotenv()

    # Retrieve API key from environment
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY is not set. Please check your .env file.")

    # Initialize the EntsoePandasClient with the API key
    client = EntsoePandasClient(api_key=api_key)
    # Set start and end times with timezone
    start = pd.Timestamp.now(tz="Europe/Copenhagen")
    end = start + pd.Timedelta(days=1)
    ts_w, ts_e = query(client, start, end)
    outfile_w, outfile_e = csv(ts_w, ts_e)
    dk_w, dk_e = data(outfile_w, outfile_e)
    graph(dk_w, dk_e)
 
def query(client, start, end): 

    # Query day-ahead prices
    ts_w = client.query_day_ahead_prices("DK_1", start=start, end=end)  # For Western Denmark
    ts_e = client.query_day_ahead_prices("DK_2", start=start, end=end)  # For Eastern Denmark

    return ts_w, ts_e

def csv(ts_w, ts_e): 
    # Reset column names
    ts_w = ts_w.reset_index()
    ts_e = ts_e.reset_index()
    ts_w.columns = ["Time", "Price"]
    ts_e.columns = ["Time", "Price"]

    # Save the results to a CSV file
    ts_w.to_csv("outfile_w.csv")
    ts_e.to_csv("outfile_e.csv")

    # Load the CSV file 
    outfile_w = pd.read_csv("outfile_w.csv")
    outfile_e = pd.read_csv("outfile_e.csv")

    return outfile_w, outfile_e

def data(outfile_w, outfile_e): 
    # Time series
    dk_w = pd.Series(
    outfile_w["Price"].values * 7.45 / 1000, # Prices
    index = outfile_w["Time"],  # Date stamps
    name = "Danmark Vest" # Name 
    )

    dk_e = pd.Series(
    outfile_e["Price"].values * 7.45 / 1000, # Prices
    index = outfile_e["Time"],  # Date stamps
    name = "Danmark Øst" # Name 
    )

    # Ensure the index is datetime
    dk_w.index = pd.to_datetime(dk_w.index)
    dk_e.index = pd.to_datetime(dk_e.index)

    # Generate interval labels
    intervals = [
        f"{time.strftime('%H.%M')}-{(time + pd.Timedelta(hours=1)).strftime('%H.%M')}"
        for time in dk_w.index
    ]

    # Update the index with the interval labels
    dk_w.index = intervals
    dk_e.index = intervals

    return dk_w, dk_e

def graph(dk_w, dk_e): 
    # Ensure dk_w and dk_e are DataFrames
    dk_w = dk_w.to_frame(name="Price").reset_index()  # Convert Series to DataFrame
    dk_w.columns = ["Time", "Price"]  # Assign column names

    dk_e = dk_e.to_frame(name="Price").reset_index()
    dk_e.columns = ["Time", "Price"]

    # Create a Plotly figure
    fig = go.Figure()

    # Add DK_west trace (visible by default)
    fig.add_trace(
        go.Bar(
            x=dk_w["Time"],
            y=dk_w["Price"],  # Use Price for y-axis
            name="Pris DKK/KWh"  # Label for the legend
        )
    )

    # Add DK_east trace (hidden by default)
    fig.add_trace(
        go.Bar(
            x=dk_e["Time"],
            y=dk_e["Price"],  # Use Price for y-axis
            name="Pris DKK/KWh",
            visible=False  # Initially hidden
        )
    )

    # Add dropdown menu
    fig.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {
                        "label": "Vest Danmark",
                        "method": "update",
                        "args": [
                            {"visible": [True, False]},  # Show DK_west, hide DK_east
                            {"title.text": "DKK/KWh timepriser - Vest Danmark"}  # Update title
                        ],
                    },
                    {
                        "label": "Øst Danmark",
                        "method": "update",
                        "args": [
                            {"visible": [False, True]},  # Show DK_east, hide DK_west
                            {"title.text": "DKK/KWh timepriser - Øst Danmark"}  # Update title
                        ],
                    },
                ],
                "direction": "down",
                "showactive": True,
                "x": 0.5,  # Center the dropdown menu
                "xanchor": "center",
                "y": 1.2,  # Place above the chart
                "yanchor": "top",
            }
        ],
        title="DKK/KWh timepriser - Vest Danmark",  # Initial title
        xaxis_title="Tid",
        yaxis_title="Pris (DKK/KWh)",
        template="plotly_white",
        legend_title="Region"
    )

    # Save the figure as an HTML file
    fig.write_html("day_ahead_prices_barchart.html")

schedule.every(1).hours.do(main)

if __name__ == "__main__":
    import time
    print("Starting hourly update scheduler...")
    main()
    while True:
        print("Checking for scheduled tasks...")
        schedule.run_pending()
        time.sleep(1)