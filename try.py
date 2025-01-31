from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
from transformers import pipeline
import re

app = Flask(__name__)

# Konfigurasi Elasticsearch
es = Elasticsearch(
    "https://elkhub.bni.co.id:443",
    api_key=("lzGp14oBDU3MdEtzHiAp:UPRNLDDqTO2elKZJALON9g"),
    verify_certs=False  # Menonaktifkan verifikasi sertifikat SSL
)

# Inisialisasi model summarization
try:
    summarizer = pipeline("summarization", model="t5-base")
except Exception as e:
    print(f"Error initializing summarizer: {e}")
    summarizer = None

def clean_message(message):
    """Membersihkan pesan log dari informasi teknis yang tidak perlu."""
    cleaned_message = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', message)
    cleaned_message = re.sub(r'\b\d{1,3}(?:\.\d{1,3}){3}(:\d{1,5})?\b', '', message)
    cleaned_message = re.sub(r'\[IPv6.*?\]', '', cleaned_message)
    cleaned_message = re.sub(r'node_id=[^\s]+', '', cleaned_message)
    cleaned_message = re.sub(r'host=[^\s]+', '', cleaned_message)
    cleaned_message = re.sub(r'api_version=\([^\)]+\)', '', cleaned_message)
    cleaned_message = re.sub(r'connecting[> ]*', '', cleaned_message)
    cleaned_message = re.sub(r'producer.*?timeout.*', 'Producer timeout error.', cleaned_message)
    cleaned_message = re.sub(r'closing connection', 'Connection closed.', cleaned_message)
    cleaned_message = re.sub(r'[^\w\s,.]', '', cleaned_message)
    return cleaned_message.strip() if len(cleaned_message.strip()) >= 50 else None

def summarize_logs(logs):
    """Merangkum log menggunakan model summarization."""
    if not summarizer:
        return "Summarizer is not initialized."
    combined_logs_text = "\n".join(logs)[:1000]
    try:
        summary = summarizer(combined_logs_text, max_length=300, min_length=100, do_sample=False)
        return summary[0]['summary_text'] if summary else "No summary generated."
    except Exception as e:
        return f"Error summarizing logs: {str(e)}"

@app.route("/summarize_logs", methods=["GET"])
def search_logs_and_summarize():
    """API untuk mengambil dan merangkum log dari Elasticsearch."""
    query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": "now-4d/d", "lt": "now/d"}}},
                    {"match": {"level": "WARNING"}}
                ]
            }
        }
    }
    
    try:
        results = scan(client=es, index="log-ocp-snap-service", query=query)
        logs = [clean_message(hit.get("_source", {}).get("_message", "")) for hit in results if clean_message(hit.get("_source", {}).get("message", ""))]
        if not logs:
            return jsonify({"summary": "No logs found for the given query."})
        summary = summarize_logs(logs)
        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
