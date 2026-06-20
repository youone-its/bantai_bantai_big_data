import os
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

builder = (
    SparkSession.builder
    .appName("medallion-db-sync")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
)
spark = configure_spark_with_delta_pip(builder).getOrCreate()
spark.sparkContext.setLogLevel("WARN")

HDFS_HOST = os.getenv("HDFS_HOST", "namenode")
HDFS_PORT = os.getenv("HDFS_PORT", "8020")
HDFS_PATH = f"hdfs://{HDFS_HOST}:{HDFS_PORT}"
GOLD = f"{HDFS_PATH}/lakehouse/gold"

# PostgreSQL configurations
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "bigdata_db")
DB_USER = os.getenv("POSTGRES_USER", "hadoop")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"

GOLD_TABLES = [
    "gold_demand_proyeksi",
    "gold_kapasitas_kecamatan",
    "gold_gap_analysis",
    "gold_rekomendasi_usb_rkb",
    "gold_school_capacity_gap_index",
    "gold_cluster_priority",
    "gold_evaluation_metrics",
    "gold_data_quality_report",
    "sby_sekolah_per_kecamatan",
    "sby_siswa_per_kecamatan",
    "sby_sd_akreditasi_summary",
    "sby_smp_akreditasi_summary",
    "sby_rasio_murid_guru",
    "sby_penduduk_usia_summary"
]

print("=" * 70)
print(" STARTING SPARK ➔ POSTGRESQL SYNC")
print("=" * 70)

for table in GOLD_TABLES:
    hdfs_path = f"{GOLD}/{table}"
    print(f"Syncing {table} from HDFS ({hdfs_path}) to Postgres...")
    try:
        df = spark.read.format("delta").load(hdfs_path)
        
        # Write to JDBC (automatically overwriting schema & data)
        df.write.format("jdbc") \
            .option("url", JDBC_URL) \
            .option("dbtable", table) \
            .option("user", DB_USER) \
            .option("password", DB_PASSWORD) \
            .option("driver", "org.postgresql.Driver") \
            .mode("overwrite") \
            .save()
        print(f"  ✅ Synced {table} successfully ({df.count()} rows)")
    except Exception as e:
        print(f"  ❌ Error syncing {table}: {e}")

print("=" * 70)
print(" SYNC COMPLETED")
print("=" * 70)
spark.stop()
