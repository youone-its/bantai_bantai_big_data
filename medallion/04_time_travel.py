"""
TIME TRAVEL — Delta Lake Version Control
========================================
Demonstrasi fitur time travel Delta Lake pada tabel Gold analitik:
  1. Baca versi saat ini + catat version id
  2. Lakukan UPDATE (menghasilkan versi baru)
  3. Baca kembali versi LAMA via option("versionAsOf", v)
  4. Tampilkan riwayat transaksi (DeltaTable.history)
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp
from delta import configure_spark_with_delta_pip
from delta.tables import DeltaTable

builder = (
    SparkSession.builder
    .appName("medallion-time-travel")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()
spark.sparkContext.setLogLevel("WARN")

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
GOLD = f"hdfs://{HDFS_HOST}:{HDFS_PORT}/lakehouse/gold"

TABLES = ["gold_gap_analysis", "gold_rekomendasi_usb_rkb"]


def demo(table):
    path = f"{GOLD}/{table}"
    print(f"\n{'-' * 70}\n Tabel: {table}\n{'-' * 70}")
    try:
        dt = DeltaTable.forPath(spark, path)
        v_before = dt.history().select("version").first()[0]
        n_before = spark.read.format("delta").load(path).count()
        print(f"  Versi saat ini : v{v_before} ({n_before} record)")

        # UPDATE -> versi baru (menambahkan kolom penanda waktu refresh)
        df = spark.read.format("delta").load(path).withColumn("_refreshed_at", current_timestamp())
        df.write.format("delta").mode("overwrite").option("mergeSchema", "true").save(path)
        v_after = DeltaTable.forPath(spark, path).history().select("version").first()[0]
        print(f"  Setelah UPDATE : v{v_after}")

        # Time travel ke versi lama
        old = spark.read.format("delta").option("versionAsOf", v_before).load(path)
        print(f"  Baca versi lama (v{v_before}) via versionAsOf : {old.count()} record")

        print("  Riwayat transaksi:")
        dt.history().select("version", "timestamp", "operation").show(5, truncate=False)
    except Exception as e:
        print(f"  GAGAL: {e} (jalankan 03_gold.py lebih dulu)")


def main():
    print("=" * 70)
    print(" TIME TRAVEL — Delta Lake Version Control")
    print("=" * 70)
    for t in TABLES:
        demo(t)
    print("=" * 70)
    print(" Time travel selesai.")
    print("=" * 70)
    spark.stop()


if __name__ == "__main__":
    main()
