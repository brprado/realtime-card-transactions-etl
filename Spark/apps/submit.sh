#!/bin/bash
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /tmp/spark-sql-kafka-0-10_2.12-3.5.3.jar,/tmp/kafka-clients-3.5.0.jar,/tmp/spark-token-provider-kafka-0-10_2.12-3.5.3.jar,/tmp/commons-pool2-2.11.1.jar,/tmp/delta-spark_2.12-3.0.0.jar,/tmp/delta-storage-3.0.0.jar,/tmp/hadoop-aws-3.3.4.jar,/tmp/aws-java-sdk-bundle-1.12.262.jar \
  /opt/spark/apps/$1
