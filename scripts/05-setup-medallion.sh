#!/bin/bash

# ============================================================================
# SETUP MEDALLION - Run Bronze, Silver, Gold, and Spark Max Value pipelines
# ============================================================================

echo "========================================================================"
echo " SETUP MEDALLION - Running Data Pipelines"
echo "========================================================================"

SPARK_CONTAINER="spark-medallion"

# Check if Spark container is running
echo ""
echo "Checking Spark container..."
if ! docker ps | grep -q "$SPARK_CONTAINER"; then
    echo "❌ Spark container is not running!"
    echo "   Run: docker-compose up -d spark"
    exit 1
fi

echo "✅ Spark container is running"

# Function to run Spark job
run_spark_job() {
    local script=$1
    local description=$2
    
    echo ""
    echo "========================================================================"
    echo " $description"
    echo "========================================================================"
    echo ""
    
    docker exec -e HADOOP_USER_NAME=hadoop $SPARK_CONTAINER spark-submit /app/$script
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ $description completed successfully!"
    else
        echo ""
        echo "❌ $description failed!"
        exit 1
    fi
}

# Run Bronze layer
run_spark_job "01_bronze.py" "BRONZE LAYER - Raw Data Ingestion"

# Run Silver layer
run_spark_job "02_silver.py" "SILVER LAYER - Data Cleaning & Transformation"

# Run Gold layer
run_spark_job "03_gold.py" "GOLD LAYER - Business Analytics"

# Run Spark Max Value Pipeline
run_spark_job "05_spark_max_value.py" "SPARK MAX VALUE - Find Max + 20%"

# Run Analysis 2 (SCGI, K-Means, Evaluation)
run_spark_job "08_analysis2.py" "ANALYSIS 2 - SCGI, K-Means & Model Evaluation"


echo ""
echo "========================================================================"
echo " ✅ ALL MEDALLION PIPELINES COMPLETED!"
echo "========================================================================"
echo ""
echo "Summary:"
echo "  🥉 Bronze: Raw data ingested from HDFS"
echo "  🥈 Silver: Data cleaned and transformed"
echo "  🥇 Gold: Business analytics created"
echo "  📊 Max Value: Max capacity + 20% calculated"
echo "  🔬 Analysis 2: SCGI, K-Means, MAPE & Evaluation metrics"
echo ""
echo "Next steps:"
echo "  - Check results: bash scripts/05-check-medallion.sh"
echo "  - Start backend: docker-compose up -d backend"
echo "  - Access API: http://localhost:8000/docs"
echo ""
