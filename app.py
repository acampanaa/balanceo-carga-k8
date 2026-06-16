import os
from flask import Flask, jsonify
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient(os.environ.get("MONGO_URI", "mongodb://mongo:27017/"))
db = client["demo"]
contador = db["contador"]

@app.route("/")
def index():
    doc = contador.find_one_and_update(
        {"_id": "global"},
        {"$inc": {"total": 1}},
        upsert=True,
        return_document=True,
    )
    return jsonify({
        "pod": os.environ.get("POD_NAME", "desconocido"),
        "peticiones_totales": doc["total"],
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
