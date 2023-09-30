import pymongo
from flask import Flask, render_template

app = Flask(__name__)

# MongoDB connection settings
mongo_client = pymongo.MongoClient("mongodb+srv://samueloppong:51UVyecsZ3sLCOPC@cluster0.52xfihh.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["container"]
appointments_collection = db["instance"]

# Route to display data from the collection
@app.route("/")
def index():
    # Retrieve all entries from the collection
    all_entries = list(appointments_collection.find())
    return render_template("index.html", entries=all_entries)

if __name__ == "__main__":
    app.run(debug=True)
