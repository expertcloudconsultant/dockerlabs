import os
import time
import random
import string
import pymongo
import docker
import subprocess
import shlex
import json

# MongoDB connection settings
mongo_client = pymongo.MongoClient("mongodb+srv://samueloppong:51UVyecsZ3sLCOPC@cluster0.52xfihh.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["container"]
appointments_collection = db["instance"]

# Docker connection
docker_client = docker.from_env()

def create_user(username, email, host_port, container_id, ssh_access_pin):
    password = generate_password()
    escaped_password = shlex.quote(password)
    ssh_username = username
    ssh_password = escaped_password
    user = {
        "username": username,
        "email": email,
        "ssh_username": ssh_username,
        "host_port": host_port,
        "container_id": container_id,
        "ssh_access_pin": ssh_access_pin,
        "password": password,  # Add password to the user entry
        "port_number": host_port  # Add port number to the user entry
    }
    # Insert the document into the MongoDB collection
    result = appointments_collection.insert_one(user)
    
    print("User data to be inserted into MongoDB:")
    print(user)

    # Insert the user information into the MongoDB collection
    write_to_mongodb(user)



def write_to_mongodb(user):
    try:
        # Insert the document into the MongoDB collection
        result = appointments_collection.insert_one(user)
        print(f"User {user['username']} inserted successfully with ID: {result.inserted_id}")
    except Exception as e:
        print(f"Error inserting document into MongoDB: {e}")


# Rest of the code remains unchanged

		

def generate_password(length=12):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# ...

def create_docker_container(username, email):
    container_name = f"user_{username}_container"
    network_name = f"{username}-network"
    host_port = get_random_port()
    remove_unused_networks()  # Remove Docker networks not attached to any container
    create_network(network_name)  # Create the network if it doesn't exist
    password = generate_password()
    build_docker_image(username, password)  # Build the Docker image with a generated password
    docker_command = f"docker run -dit --name {container_name} --network {network_name} -p {host_port}:22 {username}-ubuntu-ssh"
    try:
        container_id = subprocess.check_output(docker_command, shell=True, text=True).strip()
        print(f"Docker container '{container_name}' created.")
        print(f"SSH access: ssh -p {host_port} {username}@localhost")
        print(f"Container ID: {container_id}")
        # Pass the generated values to create_user
        create_user(username, email, host_port, container_id, password)
        return host_port, container_id, password
    except subprocess.CalledProcessError as e:
        print(f"Error creating Docker container: {e}")
        return None, None, None

# ...

def remove_unused_networks():
    unused_networks = subprocess.check_output('docker network ls --filter "dangling=true" --format "{{.Name}}"', shell=True, text=True)
    if unused_networks:
        networks = unused_networks.strip().split("\n")
        for network in networks:
            attached_containers = subprocess.check_output(f'docker network inspect -f "{{{{json .Containers}}}}" {network}', shell=True, text=True)
            if attached_containers.strip() == "[]":
                docker_command = f"docker network rm {network}"
                subprocess.run(docker_command, shell=True)
                print(f"Docker network '{network}' removed.")

def create_network(network_name):
    docker_command = f"docker network create {network_name}"
    subprocess.run(docker_command, shell=True)
    print(f"Docker network '{network_name}' created.")

def build_docker_image(username, password):
    dockerfile = f"""
    FROM alpine:latest

    RUN apk update && apk add --no-cache openssh-server python3
    RUN ssh-keygen -A
    RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
    RUN adduser -D -s /bin/ash {username}
    RUN echo '{username}:{password}' | chpasswd

    EXPOSE 22
    CMD ["/usr/sbin/sshd", "-D"]
    """

    with open(f"{username}-Dockerfile", "w") as file:
        file.write(dockerfile)

    docker_command = f"docker build -t {username}-ubuntu-ssh -f {username}-Dockerfile ."
    subprocess.run(docker_command, shell=True)
    print(f"Docker image '{username}-ubuntu-ssh' built successfully.")
    os.remove(f"{username}-Dockerfile")

def get_random_port():
    return random.randint(49152, 65535)

def update_dashboard(username, ssh_access_pin):
    # Add your code here to update the dashboard with the latest user details
    print("Updating dashboard...")
    print(f"Username: {username}")
    print(f"SSH Access Pin: {ssh_access_pin}")
    # You can use AJAX or any other method to send the updated data to the dashboard

if __name__ == "__main__":
    # Monitor the MongoDB collection for changes
    while True:
        cursor = appointments_collection.watch(full_document="updateLookup")

        for change in cursor:
            if change["operationType"] == "insert":
                new_entry = change["fullDocument"]
                name = new_entry.get("username")
                email = new_entry.get("email")  # Retrieve email from the MongoDB document

                if name:
                    create_docker_container(name, email)

        time.sleep(1)  # Add a sleep time to avoid high CPU usage while polling
