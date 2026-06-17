#TES12345
import os
import json
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp, from_json
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession

builder = (
    SparkSession.builder
    .appName("medallion-bronze")
    .config(
        "spark.sql.extensions",
        "io.delta.sql.DeltaSparkSessionExtension"
    )
    .config(
        "spark.sql.catalog.spark_catalog",
        "org.apache.spark.sql.delta.catalog.DeltaCatalog"
    )
)

spark = configure_spark_with_delta_pip(builder).getOrCreate()

print("="*70)
print(" BRONZE LAYER: Raw Data Ingestion")
print("="*70)

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
HDFS_PATH = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"

LAKEHOUSE_PATH = f"{HDFS_PATH}/lakehouse"
BRONZE_PATH = f"{LAKEHOUSE_PATH}/bronze"

HDFS_INPUT_BASE = f"{HDFS_PATH}/data/opendata-sby"

OPEN_DATA_DATASETS = [
    {"name": "penduduk_usia", "hdfs_subpath": "penduduk-usia", "bronze_table": "sby_penduduk_usia"},
    {"name": "sekolah_akreditasi", "hdfs_subpath": "sekolah-akreditasi", "bronze_table": "sby_sekolah_akreditasi"},
    {"name": "sekolah_negeri_swasta", "hdfs_subpath": "sekolah-negeri-swasta", "bronze_table": "sby_sekolah_negeri_swasta"},
    {"name": "siswa_negeri_swasta", "hdfs_subpath": "siswa-negeri-swasta", "bronze_table": "sby_siswa_negeri_swasta"},
    {"name": "sd_akreditasi_kecamatan", "hdfs_subpath": "sd-akreditasi-kecamatan", "bronze_table": "sby_sd_akreditasi_kecamatan"},
    {"name": "smp_akreditasi_kecamatan", "hdfs_subpath": "smp-akreditasi-kecamatan", "bronze_table": "sby_smp_akreditasi_kecamatan"},
    {"name": "sekolah_murid_guru_rasio", "hdfs_subpath": "sekolah-murid-guru-rasio", "bronze_table": "sby_sekolah_murid_guru_rasio"},
]

print("\n Creating sample Weather API data...")
sample_weather_api = spark.createDataFrame([
    {
        "kode_kota": "JKT",
        "nama_kota": "Jakarta",
        "temperature": 28.5,
        "humidity": 75,
        "wind_speed": 10.0,
        "weather_code": 0,
        "timestamp": "2026-05-30 14:30:00",
    },
    {
        "kode_kota": "SBY",
        "nama_kota": "Surabaya",
        "temperature": 26.2,
        "humidity": 68,
        "wind_speed": 8.5,
        "weather_code": 1,
        "timestamp": "2026-05-30 14:30:00",
    },
], schema="kode_kota string, nama_kota string, temperature double, humidity int, wind_speed double, weather_code int, timestamp string")

weather_api_bronze = sample_weather_api \
    .withColumn("_ingested_at", current_timestamp()) \
    .withColumn("_source", lit("weather-api"))

weather_api_bronze = weather_api_bronze.dropDuplicates(["kode_kota", "timestamp"])

weather_api_bronze.write.format("delta").mode("overwrite").save(f"{BRONZE_PATH}/weather_api")
print(f" Written {weather_api_bronze.count()} weather API records to Bronze")

print("\n Creating sample RSS News data...")
sample_news = spark.createDataFrame([
    {
        "judul": "Cuaca Ekstrem di Jakarta Rabu Sore",
        "link": "https://example.com/berita/1",
        "ringkasan": "Hujan deras disertai angin kuat di Jakarta",
        "sumber": "detik",
        "waktu_terbit": "2026-05-30 12:00:00",
    },
    {
        "judul": "Surabaya Alami Kenaikan Suhu",
        "link": "https://example.com/berita/2",
        "ringkasan": "Panas terik melanda Kota Pahlawan",
        "sumber": "kompas",
        "waktu_terbit": "2026-05-30 13:15:00",
    },
], schema="judul string, link string, ringkasan string, sumber string, waktu_terbit string")

news_bronze = sample_news \
    .withColumn("_ingested_at", current_timestamp()) \
    .withColumn("_source", lit("weather-rss"))

news_bronze = news_bronze.dropDuplicates(["judul", "sumber"])

news_bronze.write.format("delta").mode("overwrite").save(f"{BRONZE_PATH}/weather_rss")
print(f" Written {news_bronze.count()} news records to Bronze")

print("\n" + "="*70)
print(" Weather Bronze layer complete!")
print(f" Weather API Bronze: {BRONZE_PATH}/weather_api")
print(f" News Bronze: {BRONZE_PATH}/weather_rss")
print("="*70 + "\n")

# ============================================================================
# OPEN DATA SURABAYA: Ingest from HDFS JSON files
# ============================================================================

print("\n" + "="*70)
print(" OPEN DATA SURABAYA: Ingesting from HDFS")
print("="*70)

for ds in OPEN_DATA_DATASETS:
    name = ds["name"]
    hdfs_input = f"{HDFS_INPUT_BASE}/{ds['hdfs_subpath']}"
    bronze_output = f"{BRONZE_PATH}/{ds['bronze_table']}"
    
    print(f"\n Processing: {name}")
    print(f"  HDFS Input: {hdfs_input}")
    print(f"  Bronze Output: {bronze_output}")
    
    try:
        df_raw = spark.read.option("multiline", "true").json(hdfs_input)
        record_count = df_raw.count()
        
        if record_count > 0:
            df_bronze = df_raw \
                .withColumn("_ingested_at", current_timestamp()) \
                .withColumn("_source", lit(name)) \
                .withColumn("_hdfs_source", lit(hdfs_input))
            
            df_bronze.write.format("delta").mode("overwrite").save(bronze_output)
            print(f"  Written {record_count} records to Bronze")
        else:
            print(f"  No data found at {hdfs_input}, skipping...")
            
    except Exception as e:
        print(f"  Error processing {name}: {e}")
        print(f"  (Data may not exist yet - run producer and consumer first)")

print("\n" + "="*70)
print(" Bronze layer complete!")
print(f" Weather tables: {BRONZE_PATH}/weather_api, {BRONZE_PATH}/weather_rss")
print(f" Open Data SBY tables: {BRONZE_PATH}/sby_*")
print("="*70 + "\n")

spark.stop()
