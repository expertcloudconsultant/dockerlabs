# Import necessary modules
import os
import time
import random
import string
import pymongo
import docker
import subprocess
import shlex

# MongoDB connection settings
mongo_client = pymongo.MongoClient("mongodb+srv://samueloppong:51UVyecsZ3sLCOPC@cluster0.52xfihh.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["container"]
appointments_collection = db["instance"]

# Docker connection
docker_client = docker.from_env()

# Function to create a user and manage user data in MongoDB
def create_user(username, email, host_port, container_id, ssh_access_pin):
    # Generate a random password for the user
    password = generate_password()
    escaped_password = shlex.quote(password)
    ssh_username = username
    ssh_password = escaped_password

    # Define user data as a dictionary
    user = {
        "username": username,
        "email": email,
        "ssh_username": ssh_username,
        "host_port": host_port,
        "container_id": container_id,
        "ssh_access_pin": ssh_access_pin,
        "password": password,
        "port_number": host_port
    }

    # Check if a user with the same username exists in MongoDB
    existing_user = appointments_collection.find_one({"username": username})

    if existing_user:
        # Update the existing user entry in MongoDB
        result = appointments_collection.update_one(
            {"username": username},
            {"$set": user}
        )
        if result.modified_count > 0:
            print(f"User {username} updated successfully.")
        else:
            print(f"User {username} not updated. No changes detected.")
    else:
        # Insert a new user entry into MongoDB
        result = appointments_collection.insert_one(user)
        if result.inserted_id:
            print(f"User {username} inserted successfully with ID: {result.inserted_id}")
        else:
            print(f"Failed to insert user {username}.")

#-:

# Function to write user data to MongoDB
def write_to_mongodb(user):
    try:
        # Insert the document into the MongoDB collection
        result = appointments_collection.insert_one(user)
        print(f"User {user['username']} inserted successfully with ID: {result.inserted_id}")
    except Exception as e:
        print(f"Error inserting document into MongoDB: {e}")

#-:

# Function to generate a random password
def generate_password(length=12):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))



#Purge dangling networks
# Function to remove unused Docker networks
# Function to remove unused Docker networks
def remove_unused_networks():
    try:
        # Purge dangling networks
        docker_command = 'docker network prune -f'
        subprocess.run(docker_command, shell=True)
        print("Dangling Docker networks purged.")
    except subprocess.CalledProcessError as e:
        print(f"Error purging dangling Docker networks: {e}")


# Function to create a Docker network
def create_network(network_name):
    docker_command = f"docker network create {network_name}"
    subprocess.run(docker_command, shell=True)
    print(f"Docker network '{network_name}' created.")



# Function to create a Docker container for a user
def create_docker_container(username, email):
    container_name = f"user_{username}_container"
    network_name = f"{username}-network"
    host_port = get_random_port()
    
    # Check if the container name already exists
    existing_containers = docker_client.containers.list(all=True, filters={"name": container_name})
    if existing_containers:
        print(f"Container '{container_name}' already exists.")
        return
    
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

#-:



# Function to build a Docker image
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

# Function to get a random port number
def get_random_port():
    return random.randint(49152, 65534)

# Function to update the dashboard with user details (Placeholder)
def update_dashboard(username, ssh_access_pin):
    # Add your code here to update the dashboard with the latest user details
    print("Updating dashboard...")
    print(f"Username: {username}")
    print(f"SSH Access Pin: {ssh_access_pin}")
    # You can use AJAX or any other method to send the updated data to the dashboard

# Main block to monitor the MongoDB collection for changes
if __name__ == "__main__":
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
