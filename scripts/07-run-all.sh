#!/bin/bash

# ============================================================================
# RUN ALL - Complete Big Data Workspace Pipeline
# ============================================================================

echo "========================================================================"
echo " 🚀 RUNNING ENTIRE BIG DATA WORKSPACE"
echo "========================================================================"
echo ""
echo "This script will:"
echo "  1. Start all Docker containers"
echo "  2. Setup Kafka topics"
echo "  3. Setup HDFS directories"
echo "  4. Run Producer (fetch data from API)"
echo "  5. Run Consumer (Kafka → HDFS)"
echo "  6. Run Medallion pipelines (Bronze → Silver → Gold)"
echo "  7. Start Backend API"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Step 1: Start Docker containers
echo ""
echo "========================================================================"
echo " STEP 1: Starting Docker Containers"
echo "========================================================================"
echo ""

docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start containers!"
    exit 1
fi

echo "✅ All containers started"
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Step 2: Setup Kafka
echo ""
echo "========================================================================"
echo " STEP 2: Setting up Kafka"
echo "========================================================================"
bash scripts/01-setup-kafka.sh

# Step 3: Setup Hadoop
echo ""
echo "========================================================================"
echo " STEP 3: Setting up Hadoop HDFS"
echo "========================================================================"
bash scripts/03-setup-hadoop.sh

# Step 4: Run Producer
echo ""
echo "========================================================================"
echo " STEP 4: Running Producer (API → Kafka)"
echo "========================================================================"
echo ""
echo "Starting producer in background..."
echo "Producer will fetch data from Open Data Surabaya API and send to Kafka"
echo ""

# Run producer in background for 30 seconds to fetch data
timeout 30s python producer_ingest/producer_open_data.py &
PRODUCER_PID=$!

echo "Producer started (PID: $PRODUCER_PID)"
echo "Waiting for data to be produced..."
sleep 15

# Step 5: Run Consumer
echo ""
echo "========================================================================"
echo " STEP 5: Running Consumer (Kafka → HDFS)"
echo "========================================================================"
echo ""
echo "Starting consumer in background..."
echo "Consumer will read from Kafka and write to HDFS"
echo ""

# Run consumer in background for 30 seconds
timeout 30s python producer_ingest/consumer_to_hdfs.py &
CONSUMER_PID=$!

echo "Consumer started (PID: $CONSUMER_PID)"
echo "Waiting for data to be consumed..."
sleep 20

# Wait for producer and consumer to finish
wait $PRODUCER_PID 2>/dev/null
wait $CONSUMER_PID 2>/dev/null

echo ""
echo "✅ Producer and Consumer completed"

# Step 6: Run Medallion
echo ""
echo "========================================================================"
echo " STEP 6: Running Medallion Pipelines"
echo "========================================================================"
bash scripts/05-setup-medallion.sh

# Step 7: Start Backend API
echo ""
echo "========================================================================"
echo " STEP 7: Starting Backend API"
echo "========================================================================"
echo ""

docker-compose up -d backend

if [ $? -ne 0 ]; then
    echo "❌ Failed to start backend!"
    exit 1
fi

echo "✅ Backend API started"

# Final summary
echo ""
echo "========================================================================"
echo " ✅ BIG DATA WORKSPACE IS READY!"
echo "========================================================================"
echo ""
echo "📊 Data Flow:"
echo "  CKAN API → Kafka → HDFS → Bronze → Silver → Gold → REST API"
echo ""
echo "🔗 Access Points:"
echo "  Backend API:     http://localhost:8000"
echo "  API Docs:        http://localhost:8000/docs"
echo "  HDFS UI:         http://localhost:9870"
echo "  YARN UI:         http://localhost:8088"
echo ""
echo "📝 Useful Commands:"
echo "  Check Kafka:     bash scripts/02-check-kafka.sh"
echo "  Check Hadoop:    bash scripts/04-check-hadoop.sh"
echo "  Check Medallion: bash scripts/06-check-medallion.sh"
echo "  Stop all:        docker-compose down"
echo ""
echo "🎉 All done!"
echo ""
