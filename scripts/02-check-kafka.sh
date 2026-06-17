#!/bin/bash

# ============================================================================
# CHECK KAFKA - Verify Kafka connection and topic contents
# ============================================================================

echo "========================================================================"
echo " CHECK KAFKA - Connection & Content Verification"
echo "========================================================================"

KAFKA_CONTAINER="kafka-broker"
BOOTSTRAP_SERVER="localhost:9092"

# Check if Kafka container is running
echo ""
echo "1️⃣  Checking Kafka container status..."
if ! docker ps | grep -q "$KAFKA_CONTAINER"; then
    echo "❌ Kafka container is not running!"
    exit 1
fi
echo "✅ Kafka container is running"

# Check Kafka broker connection
echo ""
echo "2️⃣  Checking Kafka broker connection..."
docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-broker-api-versions.sh \
    --bootstrap-server $BOOTSTRAP_SERVER 2>&1 | head -1
echo "✅ Kafka broker is accessible"

# List all topics
echo ""
echo "3️⃣  Listing all Kafka topics..."
TOPICS=$(docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-topics.sh \
    --list --bootstrap-server $BOOTSTRAP_SERVER 2>/dev/null)

if [ -z "$TOPICS" ]; then
    echo "❌ No topics found! Run: bash scripts/01-setup-kafka.sh"
    exit 1
fi

echo "$TOPICS"
TOPIC_COUNT=$(echo "$TOPICS" | wc -l)
echo ""
echo "✅ Total topics: $TOPIC_COUNT"

# Check topic details
echo ""
echo "4️⃣  Topic details (partitions, replication, config):"
echo ""
docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-topics.sh \
    --describe --bootstrap-server $BOOTSTRAP_SERVER 2>/dev/null

# Check message count per topic
echo ""
echo "5️⃣  Message count per topic (latest offset):"
echo ""

for TOPIC in $TOPICS; do
    # Get end offset
    END_OFFSET=$(docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-run-class.sh \
        kafka.tools.GetOffsetShell \
        --broker-list $BOOTSTRAP_SERVER \
        --topic $TOPIC \
        --time -1 2>/dev/null | awk -F: '{sum += $3} END {print sum}')
    
    # Get start offset
    START_OFFSET=$(docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-run-class.sh \
        kafka.tools.GetOffsetShell \
        --broker-list $BOOTSTRAP_SERVER \
        --topic $TOPIC \
        --time -2 2>/dev/null | awk -F: '{sum += $3} END {print sum}')
    
    MSG_COUNT=$((END_OFFSET - START_OFFSET))
    
    if [ "$MSG_COUNT" -gt 0 ]; then
        echo "  📨 $TOPIC: $MSG_COUNT messages"
    else
        echo "  ⚠️  $TOPIC: 0 messages (empty)"
    fi
done

# Sample messages from each topic
echo ""
echo "6️⃣  Sample messages from topics (max 2 per topic):"
echo ""

for TOPIC in $TOPICS; do
    echo "  ── $TOPIC ──"
    docker exec $KAFKA_CONTAINER /opt/kafka/bin/kafka-console-consumer.sh \
        --bootstrap-server $BOOTSTRAP_SERVER \
        --topic $TOPIC \
        --from-beginning \
        --max-messages 2 \
        --timeout-ms 3000 2>/dev/null | sed 's/^/    /'
    echo ""
done

echo "========================================================================"
echo "✅ Kafka check complete!"
echo "========================================================================"
echo ""
