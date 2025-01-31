from flask import Flask, jsonify, request
from kafka import KafkaProducer, KafkaConsumer
import redis
import json

app = Flask(__name__)

# Kafka setup
producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))
consumer = KafkaConsumer('requests', bootstrap_servers='localhost:9092', auto_offset_reset='earliest', group_id='web-app', value_deserializer=lambda v: json.loads(v.decode('utf-8')))

# Redis setup
redis_client = redis.StrictRedis(host='localhost', port=6379, decode_responses=True)

# Route: Publish a message to Kafka
@app.route('/publish', methods=['POST'])
def publish():
    data = request.json
    producer.send('requests', data)
    return jsonify({"message": "Message sent to Kafka", "data": data})

# Route: Consume messages from Kafka
@app.route('/consume', methods=['GET'])
def consume():
    messages = []
    for message in consumer:
        redis_client.set(message.key, json.dumps(message.value))  # Cache data in Redis
        messages.append(message.value)
        if len(messages) >= 10:  # Limit for demo
            break
    return jsonify({"messages": messages})

# Route: Fetch cached data from Redis
@app.route('/cache/<key>', methods=['GET'])
def get_cache(key):
    cached_data = redis_client.get(key)
    if cached_data:
        return jsonify({"cached": json.loads(cached_data)})
    return jsonify({"error": "Key not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
