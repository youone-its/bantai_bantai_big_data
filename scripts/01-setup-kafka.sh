#!/bin/bash

# ============================================================================
# SETUP KAFKA - Create Kafka topics for data ingestion
# ============================================================================

echo "========================================================================"
echo " SETUP KAFKA - Creating Topics"
echo "========================================================================"

KAFKA_CONTAINER="kafka-broker"
BOOTSTRAP_SERVER="localhost:9092"

# Check if Kafka container is running
echo ""
echo "Checking Kafka container..."
if ! docker ps | grep -q "$KAFKA_CONTAINER"; then
    echo "❌ Kafka container is not running!"
    echo "   Run: docker-compose up -d kafka"
    exit 1
fi

echo "✅ Kafka container is running"

# Wait for Kafka to be ready
echo ""
echo "Waiting for Kafka to be ready..."
sleep 5

# Create topics
echo ""
echo "Creating Kafka topics..."
echo ""


# Open Data Surabaya topics
echo ""
echo "📊 Open Data Surabaya topics:"
docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-topics.sh \
    --create --topic sby-penduduk-usia \
    --partitions 3 --replication-factor 1 \
    --config retention.ms=86400000 \
    --bootstrap-server $BOOTSTRAP_SERVER 2>/dev/null || echo "   ⚠️  sby-penduduk-usia already exists"

docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-topics.sh \
    --create --topic sby-sekolah-akreditasi \
    --partitions 3 --replication-factor 1 \
    --config retention.ms=86400000 \
    --bootstrap-server $BOOTSTRAP_SERVER 2>/dev/null || echo "   ⚠️  sby-sekolah-akreditasi already exists"

docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-topics.sh \
    --create --topic sby-sekolah-negeri-swasta \
    --partitions 3 --replication-factor 1 \
    --config retention.ms=86400000 \
    --bootstrap-server $BOOTSTRAP_SERVER 2>/dev/null || echo "   ⚠️  sby-sekolah-negeri-swasta already exists"

docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-topics.sh \
    --create --topic sby-siswa-negeri-swasta \
    --partitions 3 --replication-factor 1 \
    --config retention.ms=86400000 \
    --bootstrap-server $BOOTSTRAP_SERVER 2>/dev/null || echo "   ⚠️  sby-siswa-negeri-swasta already exists"

docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-topics.sh \
    --create --topic sby-sd-akreditasi-kecamatan \
    --partitions 3 --replication-factor 1 \
    --config retention.ms=86400000 \
    --bootstrap-server $BOOTSTRAP_SERVER 2>/dev/null || echo "   ⚠️  sby-sd-akreditasi-kecamatan already exists"

docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-topics.sh \
    --create --topic sby-smp-akreditasi-kecamatan \
    --partitions 3 --replication-factor 1 \
    --config retention.ms=86400000 \
    --bootstrap-server $BOOTSTRAP_SERVER 2>/dev/null || echo "   ⚠️  sby-smp-akreditasi-kecamatan already exists"

docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-topics.sh \
    --create --topic sby-sekolah-murid-guru-rasio \
    --partitions 3 --replication-factor 1 \
    --config retention.ms=86400000 \
    --bootstrap-server $BOOTSTRAP_SERVER 2>/dev/null || echo "   ⚠️  sby-sekolah-murid-guru-rasio already exists"

# List all topics
echo ""
echo "========================================================================"
echo " All Kafka Topics"
echo "========================================================================"
docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-topics.sh \
    --list --bootstrap-server $BOOTSTRAP_SERVER

echo ""
echo "✅ Kafka setup complete!"
echo ""
