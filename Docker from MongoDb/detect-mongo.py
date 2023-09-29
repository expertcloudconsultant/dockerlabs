import os
import pymongo
import docker
import time

# MongoDB connection settings
mongo_client = pymongo.MongoClient("mongodb+srv://samueloppong:51UVyecsZ3sLCOPC@cluster0.52xfihh.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["container"]
appointments_collection = db["instance"]

# Docker connection
docker_client = docker.from_env()

def create_docker_container(name):
    try:
        # Define the container configuration
        container_config = {
            "image": "freepass-ubuntu-ssh:latest",  # Replace with your Docker image name
            "name": name,
            # Add other container options like ports, volumes, etc. as needed
        }

        # Create the Docker container
        container = docker_client.containers.create(**container_config)

        # Start the container
        container.start()

        print(f"Container '{name}' created and started successfully.")
    except Exception as e:
        print(f"Failed to create container '{name}': {str(e)}")

if __name__ == "__main__":
    # Monitor the MongoDB collection for changes
    while True:
        cursor = appointments_collection.watch(full_document="updateLookup")

        for change in cursor:
            if change["operationType"] == "insert":
                new_entry = change["fullDocument"]
                name = new_entry.get("name")

                if name:
                    create_docker_container(name)

        time.sleep(1)  # Add a sleep time to avoid high CPU usage while polling
