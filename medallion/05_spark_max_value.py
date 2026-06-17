"""
SPARK MAX VALUE PIPELINE
========================
Flow: Bronze (find max) -> Silver (max value) -> Gold (max + 20%)

Dataset: sby_sekolah_akreditasi
Field: kapasitas_pagu_siswa (kapasitas pagu siswa per sekolah)
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, max as spark_max, lit, current_timestamp
from delta.tables import DeltaTable

spark = SparkSession.builder \
    .appName("spark-max-value-pipeline") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

print("="*70)
print(" SPARK MAX VALUE PIPELINE")
print("="*70)

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
HDFS_PATH = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"

LAKEHOUSE_PATH = f"{HDFS_PATH}/lakehouse"
BRONZE_PATH = f"{LAKEHOUSE_PATH}/bronze/sby_sekolah_akreditasi"
SILVER_PATH = f"{LAKEHOUSE_PATH}/silver/sby_max_kapasitas"
GOLD_PATH = f"{LAKEHOUSE_PATH}/gold/sby_max_kapasitas_plus_20"

SOURCE_FIELD = "kapasitas_pagu_siswa"

# ============================================================================
# STEP 1: BRONZE -> Find Max Value -> SILVER
# ============================================================================

print("\n" + "="*70)
print(" STEP 1: Bronze -> Find Max Value -> Silver")
print("="*70)

print(f"\n Reading from Bronze: {BRONZE_PATH}")
print(f" Finding max value of field: {SOURCE_FIELD}")

try:
    df_bronze = spark.read.format("delta").load(BRONZE_PATH)
    bronze_count = df_bronze.count()
    print(f" Total records in Bronze: {bronze_count}")
    
    if bronze_count == 0:
        print(" No data in Bronze, exiting...")
        spark.stop()
        exit()
    
    print("\n Sample data from Bronze:")
    df_bronze.select("kode_sekolah", "nama_sekolah", "kecamatan", SOURCE_FIELD).limit(5).show(truncate=False)
    
    max_row = df_bronze.agg(spark_max(col(SOURCE_FIELD)).alias("max_value")).collect()[0]
    max_value = max_row["max_value"]
    
    print(f"\n MAX VALUE FOUND: {max_value}")
    
    df_max_detail = df_bronze.filter(col(SOURCE_FIELD) == max_value) \
        .select(
            col("kode_sekolah"),
            col("nama_sekolah"),
            col("kecamatan"),
            col("kelurahan"),
            col("tipe_sekolah"),
            col("status_sekolah"),
            col(SOURCE_FIELD).alias("kapasitas_pagu_siswa"),
            lit(max_value).alias("max_kapasitas_pagu_siswa")
        ) \
        .withColumn("_bronze_processed_at", current_timestamp())
    
    print("\n School(s) with max capacity:")
    df_max_detail.show(truncate=False)
    
    df_silver = df_bronze.agg(
        spark_max(col(SOURCE_FIELD)).alias("max_kapasitas_pagu_siswa")
    ).withColumn("_silver_created_at", current_timestamp())
    
    df_silver.write.format("delta").mode("overwrite").save(SILVER_PATH)
    
    print(f"\n Written max value to Silver: {SILVER_PATH}")
    print(f" Max capacity: {max_value}")
    
except Exception as e:
    print(f" Error in Step 1: {e}")
    spark.stop()
    exit()

# ============================================================================
# STEP 2: SILVER -> Read Max -> Add 20% -> GOLD
# ============================================================================

print("\n" + "="*70)
print(" STEP 2: Silver -> Read Max -> Add 20% -> Gold")
print("="*70)

print(f"\n Reading from Silver: {SILVER_PATH}")

try:
    df_silver = spark.read.format("delta").load(SILVER_PATH)
    
    print("\n Data in Silver:")
    df_silver.show(truncate=False)
    
    silver_max = df_silver.collect()[0]["max_kapasitas_pagu_siswa"]
    max_plus_20 = silver_max * 1.2
    
    print(f"\n Original max: {silver_max}")
    print(f" Max + 20%: {max_plus_20}")
    print(f" Increase: {max_plus_20 - silver_max}")
    
    df_gold = df_silver.withColumn(
        "max_kapasitas_plus_20_percent",
        col("max_kapasitas_pagu_siswa") * 1.2
    ).withColumn(
        "_gold_created_at",
        current_timestamp()
    )
    
    df_gold.write.format("delta").mode("overwrite").save(GOLD_PATH)
    
    print(f"\n Written to Gold: {GOLD_PATH}")
    
except Exception as e:
    print(f" Error in Step 2: {e}")
    spark.stop()
    exit()

# ============================================================================
# STEP 3: Show Final Results
# ============================================================================

print("\n" + "="*70)
print(" FINAL RESULTS")
print("="*70)

print("\n SILVER (Max Value from Bronze):")
spark.read.format("delta").load(SILVER_PATH).show(truncate=False)

print("\n GOLD (Max Value + 20%):")
spark.read.format("delta").load(GOLD_PATH).show(truncate=False)

print("\n" + "="*70)
print(" PIPELINE COMPLETE")
print("="*70)
print(f" Bronze: {BRONZE_PATH}")
print(f" Silver: {SILVER_PATH}")
print(f" Gold: {GOLD_PATH}")
print(f" Max {SOURCE_FIELD}: {max_value}")
print(f" Max + 20%: {max_plus_20}")
print("="*70 + "\n")

spark.stop()
