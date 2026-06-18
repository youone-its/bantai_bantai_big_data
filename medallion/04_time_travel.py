"""
TIME TRAVEL: Delta Lake Version Control & Data Evolution
=========================================================
Demonstrasi Delta Lake time travel untuk version control:
1. Update data pada Gold table
2. Query versi lama (sebelum update)
3. Query versi terbaru (sesudah update)
4. Bandingkan perbedaan dan print hasilnya
"""

import os
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp
from delta.tables import DeltaTable

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("medallion-time-travel") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

print("="*70)
print(" TIME TRAVEL: Delta Lake Version Control")
print("="*70)

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
HDFS_PATH = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"

LAKEHOUSE_PATH = f"{HDFS_PATH}/lakehouse"
GOLD_PATH = f"{LAKEHOUSE_PATH}/gold"

TIME_TRAVEL_TABLES = [
    {"name": "sby_sekolah_per_kecamatan", "update_col": None, "update_value": None, "unit": None},
    {"name": "sby_siswa_per_kecamatan", "update_col": None, "update_value": None, "unit": None},
]

# ============================================================================
# OPEN DATA SURABAYA: Time Travel Demo
# ============================================================================

print("\n" + "="*70)
print(" OPEN DATA SURABAYA: Time Travel Demo")
print("="*70)

for table_info in TIME_TRAVEL_TABLES:
    table_name = table_info["name"]
    table_path = f"{GOLD_PATH}/{table_name}"
    
    print(f"\n{'='*70}")
    print(f" Table: {table_name}")
    print(f"{'='*70}")
    
    try:
        print(f"\n 1. Membaca data dari {table_path}...")
        df_original = spark.read.format("delta").load(table_path)
        record_count = df_original.count()
        print(f"    Jumlah record: {record_count}")
        
        if record_count == 0:
            print("    Tidak ada data, skipping...")
            continue
        
        print("    Sampel data:")
        df_original.limit(3).show(truncate=False)
        
        delta_table = DeltaTable.forPath(spark, table_path)
        history_before = delta_table.history().select("version").collect()
        v_before = history_before[0][0] if history_before else 0
        print(f"    Version ID (sebelum): {v_before}")
        
        print(f"\n 2. Melakukan UPDATE (overwrite dengan data baru)...")
        df_updated = df_original.withColumn("_updated_at", current_timestamp())
        df_updated.write.format("delta").mode("overwrite").save(table_path)
        
        version_after = delta_table.history().select("version").collect()[0][0]
        print(f"    Version ID (sesudah): {version_after}")
        
        print(f"\n 3. TIME TRAVEL: Membaca versi lama (version {v_before})...")
        df_old = spark.read.format("delta") \
            .option("versionAsOf", v_before) \
            .load(table_path)
        print(f"    Jumlah record versi lama: {df_old.count()}")
        print("    Sampel data versi lama:")
        df_old.limit(3).show(truncate=False)
        
        print(f"\n 4. Membaca versi terbaru...")
        df_new = spark.read.format("delta").load(table_path)
        print(f"    Jumlah record versi baru: {df_new.count()}")
        print("    Sampel data versi baru:")
        df_new.limit(3).show(truncate=False)
        
        print(f"\n 5. DELTA LOG HISTORY untuk {table_name}...")
        history = delta_table.history().select("version", "timestamp", "operation").limit(5)
        history.show(truncate=False)
        
        print(f"  {table_name} Time Travel Complete!")
        
    except Exception as e:
        print(f"  Error processing {table_name}: {e}")
        print(f"  (Table may not exist yet - run 03_gold.py first)")

print("\n" + "="*70)
print(" Time Travel Demo Complete!")
print("="*70 + "\n")

spark.stop()
