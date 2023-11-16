**User Dashboard;**
```python
import pymongo

# MongoDB connection settings
mongo_client = pymongo.MongoClient("mongodb+srv://samueloppong:51UVyecsZ3sLCOPC@cluster0.52xfihh.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["container"]
appointments_collection = db["instance"]

def write_to_mongodb(username, email, lab_option):
    try:
        # Create a document to insert into the collection
        document = {
            "username": username,
            "email": email,
            "lab_option": lab_option
        }

        # Insert the document into the MongoDB collection
        result = appointments_collection.insert_one(document)

        print(f"Successfully inserted '{username}' with email '{email}' and lab option '{lab_option}' into MongoDB with document ID: {result.inserted_id}")
    except Exception as e:
        print(f"Failed to write to MongoDB: {str(e)}")

if __name__ == "__main__":
    # Take user input for the 'username' and 'email' fields
    username = input("Enter a username: ")
    email = input("Enter an email address: ")

    # Display lab options menu
    print("Lab Options:")
    print("1 - Web Server")
    print("2 - Python")
    print("3 - Ubuntu")

    # Take user input for the lab option
    lab_option = input("Enter the lab option (1, 2, or 3): ")

    # Call the function to write the input to MongoDB
    write_to_mongodb(username, email, lab_option)
```






**Backend Docker Creation Tool**
```python
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

def create_user(username, email, host_port, container_id, ssh_access_pin, lab_option):
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
        "lab_option": lab_option
    }

    # Insert the user information into the MongoDB collection
    write_to_mongodb(username)

    # Create Docker container based on lab option
    create_docker_container(username, lab_option, password)

def create_docker_container(username, lab_option, password):
    container_name = f"user_{username}_container"
    network_name = f"{username}-network"
    host_port = get_random_port()
    remove_unused_networks()  # Remove Docker networks not attached to any container
    create_network(network_name)  # Create the network if it doesn't exist

    # Escape the password for Dockerfile usage
    escaped_password = shlex.quote(password)

    # Build the Docker image with the escaped password based on lab option
    build_docker_image(username, lab_option, escaped_password)

    docker_command = f"docker run -dit --name {container_name} --network {network_name} -p {host_port}:22 {username}-{lab_option.lower()}-ssh"
    try:
        container_id = subprocess.check_output(docker_command, shell=True, text=True).strip()
        print(f"Docker container '{container_name}' created.")
        print(f"SSH access: ssh -p {host_port} {username}@localhost")
        print(f"Container ID: {container_id}")
        return host_port, container_id, password
    except subprocess.CalledProcessError as e:
        print(f"Error creating Docker container: {e}")
        return None, None, None

def generate_password():
    # Add your logic to generate a password
    # For example, you can use the secrets module to generate a random password
    password_length = 12
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(password_length))
    return password

def build_docker_image(username, lab_option, password):
    dockerfile_content = generate_dockerfile_content(lab_option, password)

    with open(f"{username}-{lab_option.lower()}-Dockerfile", "w") as file:
        file.write(dockerfile_content)

    docker_command = f"docker build -t {username}-{lab_option.lower()}-ssh -f {username}-{lab_option.lower()}-Dockerfile ."
    subprocess.run(docker_command, shell=True)
    print(f"Docker image '{username}-{lab_option.lower()}-ssh' built successfully.")
    os.remove(f"{username}-{lab_option.lower()}-Dockerfile")

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

def generate_dockerfile_content(username, lab_option, escaped_password):
    if lab_option == "1":
        # Web Server Dockerfile content
        return f"""
        FROM alpine:latest

        RUN apk update && apk add --no-cache openssh-server apache2
        RUN ssh-keygen -A
        RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
        RUN adduser -D -s /bin/ash {username}
        RUN echo '{username}:{escaped_password}' | chpasswd

        EXPOSE 22 80
        CMD ["/bin/sh", "-c", "/usr/sbin/sshd && httpd -D FOREGROUND"]
        """
    elif lab_option == "2":
        # Python Dockerfile content
        return f"""
        FROM alpine:latest

        RUN apk update && apk add --no-cache openssh-server python3
        RUN ssh-keygen -A
        RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
        RUN adduser -D -s /bin/ash {username}
        RUN echo '{username}:{escaped_password}' | chpasswd

        EXPOSE 22
        CMD ["/usr/sbin/sshd", "-D"]
        """
    elif lab_option == "3":
        # Ubuntu Dockerfile content
        return f"""
        FROM ubuntu:latest

        RUN apt-get update && apt-get install -y openssh-server
        RUN ssh-keygen -A
        RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
        RUN adduser --disabled-password --gecos '' {username}
        RUN echo '{username}:{escaped_password}' | chpasswd

        EXPOSE 22
        CMD ["/usr/sbin/sshd", "-D"]
        """
    else:
        return ""  # Add a default case or handle unknown lab options

# Modify the call to build_docker_image accordingly
def build_docker_image(username, lab_option, password):
    dockerfile_content = generate_dockerfile_content(username, lab_option, password)

    with open(f"{username}-{lab_option.lower()}-Dockerfile", "w") as file:
        file.write(dockerfile_content)

    docker_command = f"docker build -t {username}-{lab_option.lower()}-ssh -f {username}-{lab_option.lower()}-Dockerfile ."
    subprocess.run(docker_command, shell=True)
    print(f"Docker image '{username}-{lab_option.lower()}-ssh' built successfully.")
    os.remove(f"{username}-{lab_option.lower()}-Dockerfile")


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
                lab_option = new_entry.get("lab_option")  # Add this line to get lab_option

                if name:
                    # Call create_docker_container with lab_option and password
                    create_docker_container(name, lab_option, generate_password())
    # Note: In this example, generate_password() is used to provide a password. You might have a different approach to get or generate passwords.

        time.sleep(1)  # Add a sleep time to avoid high CPU usage while polling

```
