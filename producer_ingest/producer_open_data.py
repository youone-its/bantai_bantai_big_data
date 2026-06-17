import json
import time
import requests
from datetime import datetime
from kafka import KafkaProducer

CKAN_BASE_URL = "https://ckan.surabaya.go.id/api/3/action/datastore_search"

DATASETS = [
    {
        "resource_id": "1d18fbc9-c0ac-458b-807f-8a4cafbf6d0e",
        "topic": "sby-penduduk-usia",
        "key": "penduduk-usia",
        "label": "Jumlah Penduduk Usia 7-12 Tahun"
    },
    {
        "resource_id": "0ed9224a-ebef-4c53-ad6e-f9fd1c859747",
        "topic": "sby-sekolah-akreditasi",
        "key": "sekolah-akreditasi",
        "label": "Jumlah SD/MI Terakreditasi"
    },
    {
        "resource_id": "c329aa5b-51a5-49cf-b798-9ab9946e069b",
        "topic": "sby-sekolah-negeri-swasta",
        "key": "sekolah-negeri-swasta",
        "label": "Sekolah Negeri & Swasta per Kecamatan"
    },
    {
        "resource_id": "fc3e73a2-7a09-4593-a296-0724bbb36871",
        "topic": "sby-siswa-negeri-swasta",
        "key": "siswa-negeri-swasta",
        "label": "Jumlah Siswa Negeri & Swasta per Kecamatan"
    },
    {
        "resource_id": "22d6e3c4-b786-4443-bdfa-471b827ff717",
        "topic": "sby-sd-akreditasi-kecamatan",
        "key": "sd-akreditasi-kecamatan",
        "label": "Banyaknya SD Menurut Akreditasi per Kecamatan"
    },
    {
        "resource_id": "f3028b0e-c2c4-4450-85be-b3b69af2448c",
        "topic": "sby-smp-akreditasi-kecamatan",
        "key": "smp-akreditasi-kecamatan",
        "label": "Banyaknya SMP Menurut Akreditasi per Kecamatan"
    },
    {
        "resource_id": "9b1f7b53-6be6-4c5b-bfb9-dd41cf16a096",
        "topic": "sby-sekolah-murid-guru-rasio",
        "key": "sekolah-murid-guru-rasio",
        "label": "Sekolah, Murid, Guru & Rasio per Kecamatan"
    }
]

BATCH_SIZE = 100
POLLING_INTERVAL = 3600

def fetch_ckan_data(resource_id, offset=0, limit=BATCH_SIZE):
    params = {
        "resource_id": resource_id,
        "limit": limit,
        "offset": offset
    }

    try:
        response = requests.get(CKAN_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            return data["result"]
        return None
    except Exception as e:
        print(f"  Error fetching CKAN API: {e}")
        return None

def run_producer():
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=lambda x: json.dumps(x).encode('utf-8'),
        key_serializer=lambda x: x.encode('utf-8')
    )

    print(f"Starting Open Data Surabaya Producer...")
    print(f"CKAN API: {CKAN_BASE_URL}")
    print(f"Datasets: {len(DATASETS)}")
    print(f"Polling interval: {POLLING_INTERVAL}s")
    print("-" * 50)

    try:
        while True:
            for ds in DATASETS:
                resource_id = ds["resource_id"]
                topic = ds["topic"]
                key = ds["key"]
                label = ds["label"]

                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching: {label}")
                print(f"  Resource ID: {resource_id}")
                print(f"  Topic: {topic}")

                offset = 0
                total_sent = 0

                while True:
                    result = fetch_ckan_data(resource_id, offset=offset, limit=BATCH_SIZE)

                    if not result or not result.get("records"):
                        break

                    records = result["records"]
                    total_records = result.get("total", 0)

                    for record in records:
                        record.pop("_id", None)
                        record["source_resource_id"] = resource_id
                        record["ingested_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        producer.send(topic, key=key, value=record)
                        total_sent += 1

                    print(f"  Fetched batch: offset={offset}, batch_size={len(records)}, total_so_far={total_sent}/{total_records}")

                    if offset + len(records) >= total_records:
                        break

                    offset += len(records)

                producer.flush()
                print(f"  Done! Total sent to Kafka: {total_sent} records")

            print(f"\n{'=' * 50}")
            print(f"Waiting for {POLLING_INTERVAL} seconds before next fetch...")
            time.sleep(POLLING_INTERVAL)

    except KeyboardInterrupt:
        print("\nProducer stopped by user.")
    finally:
        producer.close()
        print("Producer closed.")

if __name__ == "__main__":
    run_producer()
