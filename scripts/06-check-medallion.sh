#!/bin/bash

# ============================================================================
# CHECK MEDALLION - Verify contents of Bronze, Silver, and Gold layers
# ============================================================================

echo "========================================================================"
echo " CHECK MEDALLION - Lakehouse Layer Verification"
echo "========================================================================"

HADOOP_CONTAINER="hadoop-namenode"
SPARK_CONTAINER="spark-medallion"

# Check if containers are running
echo ""
echo "Checking containers..."
if ! docker ps | grep -q "$HADOOP_CONTAINER"; then
    echo "❌ Hadoop namenode is not running!"
    exit 1
fi
echo "✅ Hadoop namenode is running"

# Function to check Delta table
check_delta_table() {
    local layer=$1
    local table=$2
    local path="/lakehouse/$layer/$table"
    
    echo ""
    echo "  ── $table ──"
    
    # Check if table exists
    FILE_COUNT=$(docker exec $HADOOP_CONTAINER hdfs dfs -ls $path 2>/dev/null | grep -c "\.parquet\|\.delta")
    
    if [ "$FILE_COUNT" -eq 0 ]; then
        echo "    ⚠️  Table not found or empty"
        return
    fi
    
    echo "    Path: $path"
    echo "    Files: $FILE_COUNT"
    
    # Try to get record count using Spark
    if docker ps | grep -q "$SPARK_CONTAINER"; then
        RECORD_COUNT=$(docker exec $SPARK_CONTAINER pyspark --conf "spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension" --conf "spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog" -c "
from delta.tables import *
df = spark.read.format('delta').load('$path')
print(df.count())
" 2>/dev/null | tail -1)
        
        if [ -n "$RECORD_COUNT" ] && [ "$RECORD_COUNT" -eq "$RECORD_COUNT" ] 2>/dev/null; then
            echo "    Records: $RECORD_COUNT"
        fi
    fi
    
    # Show sample data
    echo "    Sample (first 3 rows):"
    docker exec $HADOOP_CONTAINER hdfs dfs -cat $path/*.parquet 2>/dev/null | head -3 | sed 's/^/      /'
}

# Check Bronze layer
echo ""
echo "========================================================================"
echo " 🥉 BRONZE LAYER - Raw Data"
echo "========================================================================"

BRONZE_TABLES=(
    "sby_penduduk_usia"
    "sby_sekolah_akreditasi"
    "sby_sekolah_negeri_swasta"
    "sby_siswa_negeri_swasta"
    "sby_sd_akreditasi_kecamatan"
    "sby_smp_akreditasi_kecamatan"
    "sby_sekolah_murid_guru_rasio"
)

for TABLE in "${BRONZE_TABLES[@]}"; do
    check_delta_table "bronze" "$TABLE"
done

# Check Silver layer
echo ""
echo "========================================================================"
echo " 🥈 SILVER LAYER - Cleaned Data"
echo "========================================================================"

SILVER_TABLES=(
    "sby_penduduk_usia"
    "sby_sekolah_akreditasi"
    "sby_sekolah_negeri_swasta"
    "sby_siswa_negeri_swasta"
    "sby_sd_akreditasi_kecamatan"
    "sby_smp_akreditasi_kecamatan"
    "sby_sekolah_murid_guru_rasio"
)

for TABLE in "${SILVER_TABLES[@]}"; do
    check_delta_table "silver" "$TABLE"
done

# Check Gold layer
echo ""
echo "========================================================================"
echo " 🥇 GOLD LAYER - Business Analytics"
echo "========================================================================"

GOLD_TABLES=(
    "sby_sekolah_per_kecamatan"
    "sby_siswa_per_kecamatan"
    "sby_sd_akreditasi_summary"
    "sby_smp_akreditasi_summary"
    "sby_rasio_murid_guru"
    "sby_penduduk_usia_summary"
    "sby_max_kapasitas_plus_20"
)

for TABLE in "${GOLD_TABLES[@]}"; do
    check_delta_table "gold" "$TABLE"
done

# Summary
echo ""
echo "========================================================================"
echo " 📊 SUMMARY"
echo "========================================================================"
echo ""

echo "Bronze tables: ${#BRONZE_TABLES[@]}"
echo "Silver tables: ${#SILVER_TABLES[@]}"
echo "Gold tables: ${#GOLD_TABLES[@]}"

echo ""
echo "HDFS Storage:"
docker exec $HADOOP_CONTAINER hdfs dfs -du -h /lakehouse 2>/dev/null | sed 's/^/  /'

echo ""
echo "========================================================================"
echo "✅ Medallion check complete!"
echo "========================================================================"
echo ""
