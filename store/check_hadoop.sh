echo "=== Raw Data from Kafka Consumer ==="
docker exec -it hadoop-namenode hdfs dfs -ls -R /data/weather/api/
docker exec -it hadoop-namenode hdfs dfs -ls -R /data/weather/rss/

echo ""
echo "=== Open Data Surabaya ==="
docker exec -it hadoop-namenode hdfs dfs -ls -R /data/opendata-sby/

echo ""
echo "=== Medallion Lakehouse ==="
docker exec -it hadoop-namenode hdfs dfs -ls -R /lakehouse/bronze/
docker exec -it hadoop-namenode hdfs dfs -ls -R /lakehouse/silver/
docker exec -it hadoop-namenode hdfs dfs -ls -R /lakehouse/gold/

