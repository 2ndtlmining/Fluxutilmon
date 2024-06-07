import requests
import json
import os
from datetime import datetime

def get_running_apps():
    url = "https://stats.runonflux.io/fluxinfo?projection=apps.runningapps.Image"
    response = requests.get(url)
    data = response.json()
    dataset = data['data']

    image_counts = {}
    total_count = 0
    for item in dataset:
        if "apps" in item and "runningapps" in item["apps"]:
            for app in item["apps"]["runningapps"]:
                image = app["Image"]
                if image not in ["containrrr/watchtower:latest", "containrrr/watchtower"]:
                    if image in image_counts:
                        image_counts[image] += 1
                    else:
                        image_counts[image] = 1
                    total_count += 1

    sorted_counts = sorted(image_counts.items(), key=lambda x: x[1], reverse=True)

    current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    file_name = f'data/docker_count_{current_time}.json'
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    existing_data = {}
    
    if os.path.exists(file_name):
        with open(file_name, 'r') as f:
            existing_data = json.load(f)
    existing_data["Snapshot"] = current_time
    existing_data["Total Docker Count"] = total_count
    existing_data["ImageCounts"] = image_counts
    with open(file_name, 'w') as f:
        json.dump(existing_data, f, indent=4)


    print(f'Data written to {file_name}')
    print(f"Total running apps: {total_count}")
    for i, (image, count) in enumerate(sorted_counts, start=1):
        print(f"{i}. {image}: {count}")

get_running_apps()