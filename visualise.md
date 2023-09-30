```css
/* styles.css */

/* Style the table */
table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 20px;
}

/* Style the table header */
th {
    background-color: #f2f2f2;
}

th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}

/* Add hover effect to table rows */
tr:hover {
    background-color: #f5f5f5;
}

```



```html
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Display Data</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    </head>
<body>
    <h1>Data from MongoDB Collection</h1>
    <table>
        <thead>
            <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Container ID</th>
                <th>Host Port</th>
                <th>Password</th>
                <th>Port Number</th>
                <th>SSH Access Pin</th>
                <th>SSH Username</th>
            </tr>
        </thead>
        <tbody>
            {% for entry in entries %}
            <tr>
                <td>{{ entry.username }}</td>
                <td>{{ entry.email }}</td>
                <td>{{ entry.container_id }}</td>
                <td>{{ entry.host_port }}</td>
                <td>{{ entry.password }}</td>
                <td>{{ entry.port_number }}</td>
                <td>{{ entry.ssh_access_pin }}</td>
                <td>{{ entry.ssh_username }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
```


```py
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

```
