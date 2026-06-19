#!/bin/bash

# ============================================================================
# CHECK HADOOP - Verify HDFS connection and directory contents
# ============================================================================

echo "========================================================================"
echo " CHECK HADOOP - HDFS Connection & Content Verification"
echo "========================================================================"

HADOOP_CONTAINER="hadoop-namenode"

# Check if Hadoop containers are running
echo ""
echo "1️⃣  Checking Hadoop containers..."
if ! docker ps | grep -q "$HADOOP_CONTAINER"; then
    echo "❌ Hadoop namenode is not running!"
    exit 1
fi
echo "✅ Hadoop namenode is running"

# Check datanode
if docker ps | grep -q "hadoop-datanode"; then
    echo "✅ Hadoop datanode is running"
else
    echo "⚠️  Hadoop datanode is not running"
fi

# Check HDFS health
echo ""
echo "2️⃣  HDFS Health Report:"
echo ""
docker exec $HADOOP_CONTAINER hdfs dfsadmin -report 2>/dev/null | grep -E "Name:|Configured Capacity:|DFS Used:|DFS Used%:|DFS Remaining:|DFS Remaining%:|Live datanodes" | sed 's/^/  /'

# Check directory structure
echo ""
echo "3️⃣  HDFS Directory Structure:"
echo ""

echo ""
echo "  📁 /data/opendata-sby/ (Open Data Surabaya - Raw from Kafka):"
docker exec $HADOOP_CONTAINER hdfs dfs -ls -R /data/opendata-sby/ 2>/dev/null | sed 's/^/    /' || echo "    (empty or not found)"

echo ""
echo "  📁 /lakehouse/bronze/ (Medallion Bronze Layer):"
docker exec $HADOOP_CONTAINER hdfs dfs -ls -R /lakehouse/bronze/ 2>/dev/null | sed 's/^/    /' || echo "    (empty or not found)"

echo ""
echo "  📁 /lakehouse/silver/ (Medallion Silver Layer):"
docker exec $HADOOP_CONTAINER hdfs dfs -ls -R /lakehouse/silver/ 2>/dev/null | sed 's/^/    /' || echo "    (empty or not found)"

echo ""
echo "  📁 /lakehouse/gold/ (Medallion Gold Layer):"
docker exec $HADOOP_CONTAINER hdfs dfs -ls -R /lakehouse/gold/ 2>/dev/null | sed 's/^/    /' || echo "    (empty or not found)"

# Count files per directory
echo ""
echo "4️⃣  File Count Summary:"
echo ""

count_files() {
    local path=$1
    local count=$(docker exec $HADOOP_CONTAINER hdfs dfs -count $path 2>/dev/null | awk '{print $2}')
    echo "  $path: ${count:-0} files"
}

count_files "/data/opendata-sby"
count_files "/lakehouse/bronze"
count_files "/lakehouse/silver"
count_files "/lakehouse/gold"

# Check HDFS disk usage
echo ""
echo "5️⃣  HDFS Disk Usage:"
echo ""
docker exec $HADOOP_CONTAINER hdfs dfs -du -h / 2>/dev/null | sed 's/^/  /'

echo ""
echo "========================================================================"
echo "✅ Hadoop check complete!"
echo "========================================================================"
echo ""
