# dockerlabs

The provided code appears to be a Python script for managing Docker containers and MongoDB entries for user accounts. It listens for changes in a MongoDB collection and, when a new user entry is added, it creates a Docker container for that user.

Here's an overview of what this script does:

1. It imports various Python modules, including `os`, `time`, `random`, `string`, `pymongo`, `docker`, `subprocess`, and `shlex`.

2. It establishes a connection to a MongoDB database using the PyMongo library.

3. It establishes a connection to the Docker daemon using the Docker library.

4. There are functions for creating a user, writing user data to MongoDB, generating a random password, creating a Docker container for a user, and managing Docker networks and images.

5. The `remove_unused_networks` function checks for and removes Docker networks that are not attached to any containers. If networks are still attached to containers, it disconnects the containers before removing the network.

6. The `create_network` function creates a Docker network if it doesn't already exist.

7. The `build_docker_image` function generates a Dockerfile, builds a Docker image based on that file, and then removes the Dockerfile.

8. The `get_random_port` function generates a random port number within a specific range.

9. The `update_dashboard` function is a placeholder for updating a dashboard with user details. It currently prints the username and SSH access pin.

10. In the main block, the script enters an infinite loop to monitor the MongoDB collection for changes. When a new user entry is added, it calls the `create_docker_container` function to create a Docker container for that user.

Please note that this script is intended to run continuously, monitoring the MongoDB collection for changes. When a new user entry is detected, it creates a Docker container for that user and updates the dashboard (though the actual implementation of dashboard updating is missing in the code). The script also takes care of managing Docker networks and images.

Make sure you have the necessary Python libraries (`pymongo` and `docker`) installed and that your Docker daemon is running for this script to work correctly. Additionally, you'll need to set up the MongoDB database and provide the appropriate MongoDB connection settings.



```python
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
```



Certainly! Here are some suggestions to enhance the given applications:

### App 1:

1. **Error Handling:**
   - Enhance the error handling in the `write_to_mongodb` function. Provide more informative error messages and log the errors for better troubleshooting.

2. **User Input Validation:**
   - Implement input validation for the `username` and `email` fields. Ensure that the inputs meet the required criteria before attempting to write to the MongoDB collection.

3. **Logging:**
   - Integrate a logging mechanism to capture important events and information. This will help in debugging and monitoring the application.

4. **Security:**
   - Consider encrypting sensitive information before storing it in the database. Implement proper security measures to protect user data.

### App 2:

1. **Modularize Code:**
   - Break down the `create_user` function into smaller, more modular functions. This improves code readability and makes it easier to maintain.

2. **Use MongoDB `_id`:**
   - Utilize the default MongoDB `_id` field in the user documents. This field is automatically generated and provides a unique identifier for each document.

3. **SSH Key Generation:**
   - Instead of using passwords for SSH access, consider implementing SSH key-based authentication. This enhances security.

4. **Container Management:**
   - Implement functions to stop and remove containers when they are no longer needed. This helps in cleaning up resources and avoiding unnecessary consumption.

5. **Documentation:**
   - Add comments to explain complex logic and document function parameters. This will be beneficial for anyone maintaining or extending the code.

6. **Dashboard Integration:**
   - Complete the `update_dashboard` function by adding the necessary code to update the dashboard with the latest user details. This could involve using a web framework, database, or any other method depending on your application architecture.

7. **Configuration Management:**
   - Consider using a configuration file or environment variables for storing sensitive information like database connection strings and API keys. This enhances security and makes it easier to manage configuration changes.

8. **Exception Handling:**
   - Improve the exception handling throughout the code. Provide meaningful error messages and handle exceptions gracefully to prevent application crashes.

9. **Code Structure:**
   - Consider organizing the code into classes and methods to improve overall structure and maintainability.

10. **Unit Testing:**
    - Implement unit tests for critical functions to ensure that they work as expected. This helps catch bugs early in the development process.

Remember to adapt these suggestions based on the specific requirements and constraints of your applications.
