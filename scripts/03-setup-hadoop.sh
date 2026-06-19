#!/bin/bash

# ============================================================================
# SETUP HADOOP - Create HDFS directories for data pipeline
# ============================================================================

echo "========================================================================"
echo " SETUP HADOOP - Creating HDFS Directories"
echo "========================================================================"

HADOOP_CONTAINER="hadoop-namenode"

# Check if Hadoop containers are running
echo ""
echo "Checking Hadoop containers..."
if ! docker ps | grep -q "$HADOOP_CONTAINER"; then
    echo "❌ Hadoop namenode is not running!"
    echo "   Run: docker-compose up -d namenode datanode"
    exit 1
fi

echo "✅ Hadoop namenode is running"

# Wait for HDFS to be ready
echo ""
echo "Waiting for HDFS to be ready..."
sleep 5

# Check HDFS health
echo ""
echo "Checking HDFS health..."
docker exec $HADOOP_CONTAINER hdfs dfsadmin -report 2>/dev/null | grep -E "Name:|Configured Capacity:|DFS Used:|Available:" | head -4
echo ""


# Create directories for Open Data Surabaya
echo ""
echo "Creating HDFS directories for Open Data Surabaya..."
docker exec $HADOOP_CONTAINER hdfs dfs -mkdir -p /data/opendata-sby/penduduk-usia
docker exec $HADOOP_CONTAINER hdfs dfs -mkdir -p /data/opendata-sby/sekolah-akreditasi
docker exec $HADOOP_CONTAINER hdfs dfs -mkdir -p /data/opendata-sby/sekolah-negeri-swasta
docker exec $HADOOP_CONTAINER hdfs dfs -mkdir -p /data/opendata-sby/siswa-negeri-swasta
docker exec $HADOOP_CONTAINER hdfs dfs -mkdir -p /data/opendata-sby/sd-akreditasi-kecamatan
docker exec $HADOOP_CONTAINER hdfs dfs -mkdir -p /data/opendata-sby/smp-akreditasi-kecamatan
docker exec $HADOOP_CONTAINER hdfs dfs -mkdir -p /data/opendata-sby/sekolah-murid-guru-rasio
echo "  ✅ /data/opendata-sby/*"

# Create directories for Medallion Lakehouse
echo ""
echo "Creating HDFS directories for Medallion Lakehouse..."
docker exec $HADOOP_CONTAINER hdfs dfs -mkdir -p /lakehouse/bronze
docker exec $HADOOP_CONTAINER hdfs dfs -mkdir -p /lakehouse/silver
docker exec $HADOOP_CONTAINER hdfs dfs -mkdir -p /lakehouse/gold
echo "  ✅ /lakehouse/*"

# Verify directories
echo ""
echo "========================================================================"
echo " Verifying HDFS Directory Structure"
echo "========================================================================"
echo ""
echo "📁 /data/:"
docker exec $HADOOP_CONTAINER hdfs dfs -ls -R /data/ 2>/dev/null | grep "^d" | sed 's/^/  /'

echo ""
echo "📁 /lakehouse/:"
docker exec $HADOOP_CONTAINER hdfs dfs -ls -R /lakehouse/ 2>/dev/null | grep "^d" | sed 's/^/  /'

echo ""
echo "========================================================================"
echo "✅ Hadoop setup complete!"
echo "========================================================================"
echo ""
