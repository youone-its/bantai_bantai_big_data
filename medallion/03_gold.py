#tes123
"""
GOLD LAYER: Business Analytics & Aggregations
============================================
Membuat table Gold dengan agregasi dan analisis:
1. Open Data Surabaya analytics (sekolah, siswa, akreditasi)
"""

import os
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, current_timestamp, count
)
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
print(" GOLD LAYER: Business Analytics & Aggregations")
print("="*70)

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
HDFS_PATH = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"

LAKEHOUSE_PATH = f"{HDFS_PATH}/lakehouse"
SILVER_PATH = f"{LAKEHOUSE_PATH}/silver"
GOLD_PATH = f"{LAKEHOUSE_PATH}/gold"

OPEN_DATA_GOLD_TABLES = [
    {"silver": "sby_sekolah_negeri_swasta", "gold": "sby_sekolah_per_kecamatan"},
    {"silver": "sby_siswa_negeri_swasta", "gold": "sby_siswa_per_kecamatan"},
    {"silver": "sby_sd_akreditasi_kecamatan", "gold": "sby_sd_akreditasi_summary"},
    {"silver": "sby_smp_akreditasi_kecamatan", "gold": "sby_smp_akreditasi_summary"},
    {"silver": "sby_sekolah_murid_guru_rasio", "gold": "sby_rasio_murid_guru"},
]

# ============================================================================
# OPEN DATA SURABAYA: Business Analytics
# ============================================================================

print("\n" + "="*70)
print(" OPEN DATA SURABAYA: Business Analytics")
print("="*70)

for ds in OPEN_DATA_GOLD_TABLES:
    silver_table = ds["silver"]
    gold_table = ds["gold"]
    silver_input = f"{SILVER_PATH}/{silver_table}"
    gold_output = f"{GOLD_PATH}/{gold_table}"
    
    print(f"\n Creating: {gold_table}")
    print(f"  Silver Input: {silver_input}")
    print(f"  Gold Output: {gold_output}")
    
    try:
        df_silver = spark.read.format("delta").load(silver_input)
        record_count = df_silver.count()
        print(f"  Read {record_count} records from Silver")
        
        if record_count == 0:
            print(f"  No data, skipping...")
            continue
        
        df_gold = df_silver.withColumn("_gold_created_at", current_timestamp())
        
        df_gold.write.format("delta").mode("overwrite").save(gold_output)
        print(f"  Written {df_gold.count()} records to Gold")
        
    except Exception as e:
        print(f"  Error processing {silver_table}: {e}")
        print(f"  (Silver data may not exist yet)")

print("\n  Creating: sby_penduduk_usia_summary")
try:
    df_penduduk = spark.read.format("delta").load(f"{SILVER_PATH}/sby_penduduk_usia")
    if df_penduduk.count() > 0:
        penduduk_summary = df_penduduk \
            .withColumn("_gold_created_at", current_timestamp())
        penduduk_summary.write.format("delta").mode("overwrite").save(f"{GOLD_PATH}/sby_penduduk_usia_summary")
        print(f"  Written {penduduk_summary.count()} records to Gold")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "="*70)
print(" Gold layer complete!")
print(f" Open Data SBY tables: {GOLD_PATH}/sby_*")
print("="*70 + "\n")

spark.stop()
