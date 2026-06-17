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
    {"name": "weather_analytics", "update_col": "temp_current", "update_value": 5.0, "unit": "°C"},
    {"name": "sby_sekolah_per_kecamatan", "update_col": None, "update_value": None, "unit": None},
    {"name": "sby_siswa_per_kecamatan", "update_col": None, "update_value": None, "unit": None},
]

# ============================================================================
# WEATHER ANALYTICS TIME TRAVEL
# ============================================================================

print("\n" + "="*70)
print(" WEATHER ANALYTICS: Time Travel Demo")
print("="*70)

print("\n 1. Membaca versi SEBELUM update...")
try:
    weather_analytics_v0 = spark.read.format("delta").load(f"{GOLD_PATH}/weather_analytics")
    print(f"\n Versi awal - jumlah record: {weather_analytics_v0.count()}")
    print("Sampel data awal:")
    weather_analytics_v0.limit(5).show(truncate=False)
    
    delta_table = DeltaTable.forPath(spark, f"{GOLD_PATH}/weather_analytics")
    version_before = delta_table.history().select("version").collect()
    if version_before:
        v_before = version_before[0][0]
        print(f" Version ID (sebelum): {v_before}")
    
except Exception as e:
    print(f"  Error membaca data awal: {e}")
    v_before = 0

print("\n 2. Melakukan UPDATE pada weather_analytics...")
try:
    delta_table = DeltaTable.forPath(spark, f"{GOLD_PATH}/weather_analytics")
    
    delta_table.update(
        condition="temp_current IS NOT NULL",
        set={"temp_current": col("temp_current") + 5.0}
    )
    
    print(" Update selesai: +5°C untuk semua readings")
    
    version_after = delta_table.history().select("version").collect()[0][0]
    print(f" Version ID (sesudah): {version_after}")
    
except Exception as e:
    print(f"  Error melakukan update: {e}")
    version_after = v_before

print("\n 3. Membaca versi SESUDAH update (latest)...")
try:
    weather_analytics_latest = spark.read.format("delta").load(f"{GOLD_PATH}/weather_analytics")
    print(f"\n Versi terbaru - jumlah record: {weather_analytics_latest.count()}")
    print("Sampel data setelah update (+5°C):")
    weather_analytics_latest.limit(5).show(truncate=False)
    
except Exception as e:
    print(f"  Error membaca data terbaru: {e}")

print("\n 4. TIME TRAVEL: Membaca versi LAMA (sebelum update)...")
try:
    if v_before != version_after:
        weather_analytics_old = spark.read.format("delta") \
            .option("versionAsOf", v_before) \
            .load(f"{GOLD_PATH}/weather_analytics")
        
        print(f"\n Versi lama (version {v_before}) - jumlah record: {weather_analytics_old.count()}")
        print("Sampel data versi lama (original temperature):")
        weather_analytics_old.limit(5).show(truncate=False)
    else:
        print("  Tidak ada perubahan versi (update mungkin gagal)")
        weather_analytics_old = weather_analytics_latest
        
except Exception as e:
    print(f"  Error time travel: {e}")

print("\n 5. PERBANDINGAN: Versi Lama vs Baru...")
try:
    old_renamed = weather_analytics_old \
        .select(col("temp_current").alias("temp_old"), "kode_kota", "timestamp")
    
    new_renamed = weather_analytics_latest \
        .select(col("temp_current").alias("temp_new"), "kode_kota", "timestamp")
    
    comparison = old_renamed.join(
        new_renamed,
        on=["kode_kota", "timestamp"],
        how="inner"
    ).withColumn(
        "temp_diff",
        col("temp_new") - col("temp_old")
    )
    
    print("\n Perbandingan Temperature Old vs New:")
    comparison.limit(10).show(truncate=False)
    
    stats = comparison.agg({
        "temp_old": ["min", "max", "avg"],
        "temp_new": ["min", "max", "avg"],
        "temp_diff": ["min", "max", "avg"]
    })
    
    print("\n Summary Statistics:")
    stats.show(truncate=False)
    
except Exception as e:
    print(f"  Error comparison: {e}")

print("\n 6. DELTA LOG HISTORY...")
try:
    delta_table = DeltaTable.forPath(spark, f"{GOLD_PATH}/weather_analytics")
    
    history = delta_table.history().select("version", "timestamp", "operation", "operationParameters").limit(10)
    print("\nDelta Lake transaction history:")
    history.show(truncate=False)
    
except Exception as e:
    print(f"  Error reading history: {e}")

print("\n" + "="*70)
print(" Weather Analytics Time Travel Complete!")
print(f"   - Read versi lama (v{v_before})")
print(f"   - Update +5°C")
print(f"   - Read versi baru (v{version_after})")
print(f"   - Time travel query ke versi lama")
print(f"   - Comparison: old vs new")
print("="*70 + "\n")

# ============================================================================
# OPEN DATA SURABAYA: Time Travel Demo
# ============================================================================

print("\n" + "="*70)
print(" OPEN DATA SURABAYA: Time Travel Demo")
print("="*70)

for table_info in TIME_TRAVEL_TABLES:
    if table_info["name"] == "weather_analytics":
        continue
    
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
