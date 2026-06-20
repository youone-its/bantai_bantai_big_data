FROM apache/spark:3.5.0-python3
USER root

# Pre-download Delta Lake JARs into Spark's jars directory
# delta-spark 3.1.0 is compatible with Spark 3.5.0
ARG DELTA_VERSION=3.1.0
ARG SCALA_VERSION=2.12
ARG MAVEN_BASE=https://repo1.maven.org/maven2

RUN curl -fsSL \
    "${MAVEN_BASE}/io/delta/delta-spark_${SCALA_VERSION}/${DELTA_VERSION}/delta-spark_${SCALA_VERSION}-${DELTA_VERSION}.jar" \
    -o /opt/spark/jars/delta-spark_${SCALA_VERSION}-${DELTA_VERSION}.jar && \
    curl -fsSL \
    "${MAVEN_BASE}/io/delta/delta-storage/${DELTA_VERSION}/delta-storage-${DELTA_VERSION}.jar" \
    -o /opt/spark/jars/delta-storage-${DELTA_VERSION}.jar && \
    curl -fsSL \
    "https://jdbc.postgresql.org/download/postgresql-42.7.2.jar" \
    -o /opt/spark/jars/postgresql-42.7.2.jar

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
WORKDIR /app
COPY . /app
ENV SPARK_LOCAL_IP=127.0.0.1
ENV PYSPARK_PYTHON=python3
CMD ["/bin/bash"]
