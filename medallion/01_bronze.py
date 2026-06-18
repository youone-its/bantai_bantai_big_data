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
print(f" Open Data SBY tables: {BRONZE_PATH}/sby_*")
print("="*70 + "\n")

spark.stop()
