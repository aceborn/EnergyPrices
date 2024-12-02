from entsoe import EntsoePandasClient
from dotenv import load_dotenv
from datetime import datetime
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

    # Query data
    ts_w, ts_e = query(client, start, end)
    outfile_w, outfile_e = csv(ts_w, ts_e)
    dk_w, dk_e = data(outfile_w, outfile_e)

    # Add taxes data and generate graph 
    today = datetime.now()
    month = today.month
    taxes = table_tax(month)
    dk_w, dk_e = with_taxes(dk_w, dk_e, taxes)
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
    outfile_w["Price"].values * 7.45 / 1000, # Prices. Convert Euro MWh to DKK KWh
    index = outfile_w["Time"],  # Date stamps
    name = "Danmark Vest" # Name 
    )

    dk_e = pd.Series(
    outfile_e["Price"].values * 7.45 / 1000, # Prices. Convert Euro MWh to DKK KWh
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

def table_tax(month):
    # Generate tables and return depending on month
    
    # generate winter tax
    if month in [10, 11, 12, 1, 2, 3]: 
        Table = {
            "Time": [
                "00.00-01.00", "01.00-02.00", "02.00-03.00", "03.00-04.00",
                "04.00-05.00", "05.00-06.00", "06.00-07.00", "07.00-08.00",
                "08.00-09.00", "09.00-10.00", "10.00-11.00", "11.00-12.00",
                "12.00-13.00", "13.00-14.00", "14.00-15.00", "15.00-16.00",
                "16.00-17.00", "17.00-18.00", "18.00-19.00", "19.00-20.00",
                "20.00-21.00", "21.00-22.00", "22.00-23.00", "23.00-00.00"
            ],
            "Price": [
                0.1519, 0.1519, 0.1519, 0.1519, 0.1519, 0.1519, 0.4556, 0.4556,
                0.4556, 0.4556, 0.4556, 0.4556, 0.4556, 0.4556, 0.4556, 0.4556,
                0.4556, 1.3668, 1.3668, 1.3668, 1.3668, 0.4556, 0.4556, 0.4556
            ]
        }
    
    else: # generate summer tax
        Table = {
        "Time": [
                "00.00-01.00", "01.00-02.00", "02.00-03.00", "03.00-04.00",
                "04.00-05.00", "05.00-06.00", "06.00-07.00", "07.00-08.00",
                "08.00-09.00", "09.00-10.00", "10.00-11.00", "11.00-12.00",
                "12.00-13.00", "13.00-14.00", "14.00-15.00", "15.00-16.00",
                "16.00-17.00", "17.00-18.00", "18.00-19.00", "19.00-20.00",
                "20.00-21.00", "21.00-22.00", "22.00-23.00", "23.00-00.00"
            ],
            "Price": [
                0.1519, 0.1519, 0.1519, 0.1519, 0.1519, 0.1519, 0.2277, 0.2277,
                0.2277, 0.2277, 0.2277, 0.2277, 0.2277, 0.2277, 0.2277, 0.2277,
                0.2277, 0.5923, 0.5923, 0.5923, 0.5923, 0.2277, 0.2277, 0.2277
            ]
    }

    return Table
def with_taxes(dk_w, dk_e, taxes):
    # Convert taxes dictionary to a DataFrame for easier processing
    taxes_df = pd.DataFrame(taxes)

    # Define a function to find the corresponding tax price based on the time interval
    def get_tax_price(interval):
        # Match the interval string directly with the 'Time' column in taxes_df
        for tax_interval, price in zip(taxes_df["Time"], taxes_df["Price"]):
            if interval == tax_interval:
                return price
        return None  # Default case if no match is found

    # Apply the tax price function to the index (time intervals) of dk_w and dk_e
    dk_w = dk_w.to_frame(name="Price")  # Ensure dk_w is a DataFrame
    dk_e = dk_e.to_frame(name="Price")  # Ensure dk_e is a DataFrame
    dk_w["Tax"] = dk_w.index.map(get_tax_price)
    dk_e["Tax"] = dk_e.index.map(get_tax_price)
    dk_w["Price_with_Tax"] = dk_w["Price"] + dk_w["Tax"]
    dk_e["Price_with_Tax"] = dk_e["Price"] + dk_e["Tax"]

    return dk_w, dk_e

def graph(dk_w, dk_e):
    # Ensure dk_w and dk_e have the required columns
    dk_w = dk_w.reset_index()  # Reset the index if necessary
    dk_e = dk_e.reset_index()

    # Create a Plotly figure
    fig = go.Figure()

    # Add DK_west (Price only) trace
    fig.add_trace(
        go.Bar(
            x=dk_w["index"],
            y=dk_w["Price"],  # Use Price for y-axis
            name="Vest Danmark u. Skat",
            visible=True,  # Default visibility
            marker=dict(color="steelblue"), # Custom color
        )
    )

    # Add DK_west (Price with Tax) trace
    fig.add_trace(
        go.Bar(
            x=dk_w["index"],
            y=dk_w["Price_with_Tax"],  # Use Price with Tax for y-axis
            name="Vest Danmark m. Skat",
            visible=False,  # Hidden by default
            marker=dict(color="red"),
        )
    )

    # Add DK_east (Price only) trace
    fig.add_trace(
        go.Bar(
            x=dk_e["index"],
            y=dk_e["Price"],  # Use Price for y-axis
            name="Øst Danmark u. Skat",
            visible=False,  # Hidden by default
            marker=dict(color="steelblue"),
        )
    )

    # Add DK_east (Price with Tax) trace
    fig.add_trace(
        go.Bar(
            x=dk_e["index"],
            y=dk_e["Price_with_Tax"],  # Use Price with Tax for y-axis
            name="Øst Danmark m. Skat",
            visible=False,  # Hidden by default
            marker=dict(color="red"),
        )
    )
    
    # Add dropdown menu
    fig.update_layout(
        updatemenus=[
            {
                "buttons": [
                    {
                        "label": "Vest Danmark u. Skat",
                        "method": "update",
                        "args": [
                            {"visible": [True, False, False, False]},  # Show DK_west (Price)
                            {"title.text": "Vest Danmark u. Skat"}
                        ],
                    },
                    {
                        "label": "Vest Danmark m. Skat",
                        "method": "update",
                        "args": [
                            {"visible": [False, True, False, False]},  # Show DK_west (Price with Tax)
                            {"title.text": "Vest Danmark m. Skat"}
                        ],
                    },
                    {
                        "label": "Øst Danmark u. Skat",
                        "method": "update",
                        "args": [
                            {"visible": [False, False, True, False]},  # Show DK_east (Price)
                            {"title.text": "Øst Danmark u. Skat"}
                        ],
                    },
                    {
                        "label": "Øst Danmark m. Skat",
                        "method": "update",
                        "args": [
                            {"visible": [False, False, False, True]},  # Show DK_east (Price with Tax)
                            {"title.text": "Øst Danmark m. Skat"}
                        ],
                    },
                ],
                "direction": "down",
                "showactive": True,
                "x": 0.5,
                "xanchor": "center",
                "y": 1.2,
                "yanchor": "top",
            }
        ],
        title="Vest Danmark u. Skat",  # Default title
        xaxis_title="Time",
        yaxis_title="Price (DKK/KWh)",
        template="plotly_white",
        legend_title="Region",
    )

    # Save the figure as an HTML file
    fig.write_html("day_ahead_prices_barchart.html", full_html=False)

if __name__ == "__main__":
    main()