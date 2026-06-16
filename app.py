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

@app.route("/stress")
def stress():
    # Calcula números primos hasta 8000 para consumir CPU
    limite = 8000
    primos = [n for n in range(2, limite) if all(n % d != 0 for d in range(2, int(n**0.5) + 1))]
    return jsonify({
        "pod": os.environ.get("POD_NAME", "desconocido"),
        "primos_encontrados": len(primos),
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
