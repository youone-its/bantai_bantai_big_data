#!/bin/bash

echo "Creating HDFS directories for raw data from Kafka consumer..."

echo ""
echo "Creating HDFS directories for Open Data Surabaya..."
docker exec hadoop-namenode hdfs dfs -mkdir -p /data/opendata-sby/penduduk-usia
docker exec hadoop-namenode hdfs dfs -mkdir -p /data/opendata-sby/sekolah-akreditasi
docker exec hadoop-namenode hdfs dfs -mkdir -p /data/opendata-sby/sekolah-negeri-swasta
docker exec hadoop-namenode hdfs dfs -mkdir -p /data/opendata-sby/siswa-negeri-swasta
docker exec hadoop-namenode hdfs dfs -mkdir -p /data/opendata-sby/sd-akreditasi-kecamatan
docker exec hadoop-namenode hdfs dfs -mkdir -p /data/opendata-sby/smp-akreditasi-kecamatan
docker exec hadoop-namenode hdfs dfs -mkdir -p /data/opendata-sby/sekolah-murid-guru-rasio

echo ""
echo "Creating HDFS directories for Medallion Lakehouse..."
docker exec hadoop-namenode hdfs dfs -mkdir -p /lakehouse/bronze
docker exec hadoop-namenode hdfs dfs -mkdir -p /lakehouse/silver
docker exec hadoop-namenode hdfs dfs -mkdir -p /lakehouse/gold

echo ""
echo "Checking all directories..."
docker exec hadoop-namenode hdfs dfs -ls -R /data/
echo ""
docker exec hadoop-namenode hdfs dfs -ls -R /lakehouse/

echo ""
echo "Checking datanode..."
docker exec hadoop-namenode hdfs dfsadmin -report

echo ""
echo "Checking YARN nodes..."
docker exec hadoop-namenode yarn node -list


