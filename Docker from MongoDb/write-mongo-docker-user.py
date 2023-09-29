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
