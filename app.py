import json, glob, os
import time
import subprocess
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, callback, Output, Input
from dash_bootstrap_templates import load_figure_template
from apscheduler.schedulers.background import BackgroundScheduler
import scheduler, schedule
import logging
import datetime

load_figure_template(["cyborg", "darkly"])
logging.basicConfig(filename='app.log', level=logging.DEBUG)

# Dash app
app = Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP, dbc.themes.DARKLY])

# Generate Docker count data
def generate_docker_dataframe():
    # Get all cleaned_data.json files in the data directory
    print("Generating dataframes process started...")
    docker_files = glob.glob(os.path.join('data', 'docker*.json'))

    # Print the cleaned data files
    print(f"Cleaned data files read into report: {docker_files}")

    # Initialize empty dataframes
    df = pd.DataFrame()

    for file in docker_files:
        # Load the JSON data from the file
        with open(file) as f:
            print('Json file loaded...{file}')
            data = json.load(f)
            snapshot_date = data["Snapshot"]
            image_counts = data["ImageCounts"]
            data_list = []
            for image, count in image_counts.items():
                data_list.append({"Snapshot": snapshot_date, "Docker Name": image, "Quantity": count})
            
        # Append the data to the existing DataFrame
        df = df._append(data_list, ignore_index=True)

    # Print the DataFrame
    print(df)
    return df

# Generate Utilization Dataframe
def generate_utilization_dataframe():
    # Get all docker*.json files in the data directory
    docker_files = glob.glob(os.path.join('data', 'utilization*.json'))

    # Initialize empty dataframes
    df = pd.DataFrame()

    for file in docker_files:
        # Load the JSON data from the file
        with open(file) as f:
            data = json.load(f)
            snapshot_date = data["Snapshot"]
            metric_values = {key: value for key, value in data.items() if key not in ["Snapshot"]}
            data_list = []
            for metric, value in metric_values.items():
                data_list.append({"Snapshot": snapshot_date, "Metric": metric, "Value": value})
            
            # Append the data to the existing DataFrame
            df = df._append(data_list, ignore_index=True)

    return df


def create_dataframe_and_figure():
    # Get all cleaned_data.json files in the data directory
    print("Generating dataframes process started...")
    docker_files = glob.glob(os.path.join('data', 'docker*.json'))

    # Print the cleaned data files
    print(f"Cleaned data files read into report: {docker_files}")

    # Initialize empty dataframes
    df = pd.DataFrame(columns=['Snapshot Date', 'Total Docker Count'])

    for file in docker_files:
        # Load the JSON data from the file
        with open(file) as f:
            print(f'Json file loaded: {file}')
            data = json.load(f)
            snapshot_date = data["Snapshot"]
            total_docker_count = data["Total Docker Count"]

        # Append the data to the existing DataFrame
        df = df._append({'Snapshot Date': snapshot_date, 'Total Docker Count': total_docker_count}, ignore_index=True)

    # Sort the DataFrame by 'Snapshot Date' in ascending order
    df = df.sort_values('Snapshot Date')

    # Print the DataFrame
    print(df)

    # Create the line graph using px.line
    fig = px.line(df, x='Snapshot Date', y='Total Docker Count', title='Total Docker Count Over Time')

    return df, fig


def find_latest_util_json_file():
    # Find the latest JSON file starting with "utilization"
    logging.info("Checking latest utilization file....")
    latest_util_file = None
    latest_time = 0
    for filename in os.listdir('data'):
        if filename.startswith("utilization") and filename.endswith(".json"):
            file_path = os.path.join('data', filename)
            file_time = os.path.getmtime(file_path)
            if file_time > latest_time:
                latest_util_file = filename
                latest_time = file_time
    logging.info(f"Latest utilization file: {latest_util_file}")
    return latest_util_file

def find_latest_docker_json_file():
    logging.info("Checking latest docker file....")
    # Find the latest JSON file starting with "utilization"
    latest_docker_file = None
    latest_time = 0
    for filename in os.listdir('data'):
        if filename.startswith("docker") and filename.endswith(".json"):
            file_path = os.path.join('data', filename)
            file_time = os.path.getmtime(file_path)
            if file_time > latest_time:
                latest_docker_file = filename
                latest_time = file_time
    logging.info(f"Latest docker file: {latest_docker_file}")
    return latest_docker_file

def check_snapshot_age(json_file):
    # Read the JSON file
    logging.info(f"Checking snapshot age: {json_file}")
    file_path = os.path.join('data', json_file)
    with open(file_path, "r") as f:
        data = json.load(f)

    # Check if the snapshot date is older than 5 minutes from the current time
    snapshot_date = data.get("Snapshot")
    
    if snapshot_date:
        snapshot_time = time.mktime(time.strptime(snapshot_date, "%Y-%m-%d_%H-%M-%S"))
        current_time = time.time()
        print("Checking snapshot age...")
        print ("Snapshot date: %s, Current time: %s, Snapshot time: %s" % (snapshot_date, current_time, snapshot_time))
        if current_time - snapshot_time > 720 * 60:
            print("Snapshot is older than 12 hours")
            logging.info("Snapshot is older than 12 hours")
            return True
        else:
            print("Last snapshot is still current no need to take snapshot")
            logging.info("Last snapshot is still current no need to take snapshot")

    return False

def run_apidata():
    # Run apidata.py to create a new snapshot
    logging.info("Running apidata.py....")
    print("Running apidata.py....")
    subprocess.run(["python3", "apidata.py"])

def run_dockerdata():
    # Run apidata.py to create a new snapshot
    print("Running count_docker.py....")
    logging.info("Running count_docker.py....")
    subprocess.run(["python3", "count_docker.py"])


def check_snapshots():
    print("Checking snapshots....", flush=True)
    logging.info("Checking snapshots....")
    latest_util_file = find_latest_util_json_file()
    latest_docker_file = find_latest_docker_json_file()

    if latest_util_file:
        if check_snapshot_age(latest_util_file):
            print("Snapshot is older than 5 minutes, running apidata.py")
            logging.info("Snapshot is older than 5 minutes, running apidata.py")
            run_apidata()
            generate_utilization_dataframe()  # Reload the utilization dataframe
        else:
            print("Snapshot is not old enough, no new snapshot will be taken")
            logging.info("Snapshot is not old enough, no new snapshot will be taken")
    else:
        print("No latest file found, sleeping for 1 hour...")
        logging.info("No latest file found, sleeping for 1 hour...")
        print("Scheduler will check again in 1 hour")
        logging.info("Scheduler will check again in 1 hour")

    if latest_docker_file:
        if check_snapshot_age(latest_docker_file):
            print("Snapshot is older than 5 minutes, running count_docker.py")
            logging.info("Snapshot is older than 5 minutes, running count_docker.py")
            run_dockerdata()
            generate_docker_dataframe()  # Reload the docker dataframe
        else:
            print("Snapshot is not old enough, no new snapshot will be taken")
            logging.info("Snapshot is not old enough, no new snapshot will be taken")
    else:
        print("No latest file found, sleeping for 1 hour...")
        logging.info("No latest file found, sleeping for 1 hour...")
        print("Scheduler will check again in 1 hour")


# Create a scheduler instance
scheduler = BackgroundScheduler()

# Start the scheduler
scheduler.start()

# Check snapshots immediately
check_snapshots()



def main():
    # Start the Dash app
    app.run_server(host='0.0.0.0', port=8049, debug=True)

    # Create a scheduler instance
    scheduler = BackgroundScheduler()

    # Schedule the check_snapshots() function to run every hour
    scheduler.add_job(check_snapshots, 'interval', hours=1)

    # Start the scheduler
    scheduler.start()

    # Keep the program running
    while True:
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Scheduler is running. Current time: {current_time}")
        logging.info(f"Scheduler is running. Current time: {current_time}")
        check_snapshots()
        time.sleep(3600)
        

docker_df = generate_docker_dataframe()
dockertotal_df, fig = create_dataframe_and_figure()
utilization_df = generate_utilization_dataframe()

# Define the layout of the app
app.layout = html.Div([
    dbc.CardGroup([
        dbc.Card(
            dbc.CardBody([
                dbc.Label("Docker Name"),
                dbc.Select(
                    id='docker-dropdown',
                    options=[{'label': name, 'value': name} for name in docker_df['Docker Name'].unique()],
                    value=docker_df['Docker Name'].unique()
                )
            ]),
        ),
        dbc.Card(
            dbc.CardBody([
                dbc.Label("Utilization Metric"),
                dbc.Select(
                    id='util-dropdown',
                    options=[{'label': metric, 'value': metric} for metric in utilization_df['Metric'].unique()],
                    value=utilization_df['Metric'].unique()
                )
            ]),
        )
    ]),
    dcc.Graph(id='line-chart'),
    dcc.Graph(id='DockerTotalGraph', figure=fig),
    dcc.Graph(id='UtilGraph')
])
 
@app.callback(
    Output('UtilGraph', 'figure'),
    [Input('util-dropdown', 'value')]
)
def update_util_chart(selected_metric):
    if selected_metric is None:
        selected_metric = utilization_df['Metric'].unique()[0]
    if isinstance(selected_metric, list):
        selected_metric = selected_metric[0]
    filtered_df = utilization_df[utilization_df['Metric'] == selected_metric]
    filtered_df = filtered_df.sort_values('Snapshot') # sort by Snapshot in ascending order
    Utilfig = px.line(filtered_df, x='Snapshot', y='Value', markers=True, template='plotly_dark')
    Utilfig.update_layout(title='Utilization', xaxis_title='Snapshot', yaxis_title=selected_metric)
    logging.info("Utilization chart updated")
    return Utilfig


@app.callback(
    Output('line-chart', 'figure'),
    [Input('docker-dropdown', 'value')]
)
def update_line_chart(selected_docker_name):
    if len(selected_docker_name) == 0:
        raise ValueError("No Docker Name selected")
    
    # Convert the selected_docker_name to a list
    selected_docker_name = [selected_docker_name] if isinstance(selected_docker_name, str) else selected_docker_name
    
    # Filter the docker_df based on the selected Docker Name
    filtered_df = docker_df[docker_df['Docker Name'].isin(selected_docker_name)]
    
    # Sort the filtered_df by 'Snapshot' in ascending order
    filtered_df = filtered_df.sort_values('Snapshot')
    
    # Create the line graph using Plotly
    fig = px.line(filtered_df, x='Snapshot', y='Quantity', markers=True, template='plotly_dark')
    fig.update_layout(title='Docker Container Count', xaxis_title='Snapshot', yaxis_title='Quantity')
    logging.info("Line chart updated")
    return fig


if __name__ == "__main__":
    main()