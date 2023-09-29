
Step 1:
![image](https://github.com/expertcloudconsultant/dockerlabs/assets/69172523/0f6f2495-45fa-4925-808c-d82dff533bea)


![image](https://github.com/expertcloudconsultant/dockerlabs/assets/69172523/00b0cc29-eb82-4c22-a7a1-bce28fc8cdbb)



![image](https://github.com/expertcloudconsultant/dockerlabs/assets/69172523/43c4ff4c-fb51-4842-a758-79e413ac4f3b)




**Dashboard**
```python
import pymongo

# MongoDB connection settings
mongo_client = pymongo.MongoClient("mongodb+srv://samueloppong:51UVyecsZ3sLCOPC@cluster0.52xfihh.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["container"]
appointments_collection = db["instance"]

def write_to_mongodb(username, email):
    try:
        # Create a document to insert into the collection
        document = {
            "username": username,
            "email": email
        }

        # Insert the document into the MongoDB collection
        result = appointments_collection.insert_one(document)

        print(f"Successfully inserted '{username}' with email '{email}' into MongoDB with document ID: {result.inserted_id}")
    except Exception as e:
        print(f"Failed to write to MongoDB: {str(e)}")

if __name__ == "__main__":
    # Take user input for the 'username' and 'email' fields
    username = input("Enter a username: ")
    email = input("Enter an email address: ")

    # Call the function to write the input to MongoDB
    write_to_mongodb(username, email)

```







**Auto Generator**
```python
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
        "password": password,
        "port_number": host_port
    }

    # Check if a user with the same username exists
    existing_user = appointments_collection.find_one({"username": username})

    if existing_user:
        # Update the existing user entry
        result = appointments_collection.update_one(
            {"username": username},
            {"$set": user}
        )
        if result.modified_count > 0:
            print(f"User {username} updated successfully.")
        else:
            print(f"User {username} not updated. No changes detected.")
    else:
        # Insert a new user entry
        result = appointments_collection.insert_one(user)
        if result.inserted_id:
            print(f"User {username} inserted successfully with ID: {result.inserted_id}")
        else:
            print(f"Failed to insert user {username}.")

    # Rest of the code remains unchanged

# Rest of the code remains unchanged


    print("User data to be inserted into MongoDB:")
    print(user)

    # Insert the user information into the MongoDB collection
    #write_to_mongodb(user)

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

# Rest of the code remains unchanged


# Rest of the code remains unchanged
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
            else:
                # Network is still attached to containers, so remove them first
                containers = attached_containers.strip().split("\n")
                for container_id in containers:
                    container_id = container_id.strip('"')
                    subprocess.run(f"docker network disconnect {network} {container_id}", shell=True)
                # Now that containers are removed from the network, prune it
                docker_command = f"docker network prune {network}"
                subprocess.run(docker_command, shell=True)
                print(f"Docker network '{network}' removed after disconnecting containers.")


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
    return random.randint(49152, 65534)


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

```
