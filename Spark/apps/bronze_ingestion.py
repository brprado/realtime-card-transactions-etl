from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, current_timestamp, lit, year, month, dayofmonth
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, 
    TimestampType, MapType, BooleanType
)
import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Configurações MinIO
MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "bronze"
CHECKPOINT_PATH = f"s3a://{MINIO_BUCKET}/checkpoints/bronze"
DELTA_PATH = f"s3a://{MINIO_BUCKET}/transactions"

# Criar SparkSession com configurações para Kafka e Delta Lake
# Nota: Delta Lake requer JARs no spark-submit (veja comando abaixo)
spark = SparkSession.builder \
    .appName("BronzeIngestion") \
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_PATH) \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Configurar o acesso ao MinIO via Hadoop S3A
hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
hadoop_conf.set("fs.s3a.endpoint", f"http://{MINIO_ENDPOINT}")
hadoop_conf.set("fs.s3a.access.key", MINIO_ACCESS_KEY)
hadoop_conf.set("fs.s3a.secret.key", MINIO_SECRET_KEY)
hadoop_conf.set("fs.s3a.path.style.access", "true")  # Necessário para MinIO
hadoop_conf.set("fs.s3a.connection.ssl.enabled", "false")
hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
hadoop_conf.set("fs.s3a.aws.credentials.provider", 
                "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")

# Definir schema das transações
transaction_schema = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("account_id", StringType(), True),
    StructField("transaction_type", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("merchant", StringType(), True),
    StructField("category", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("location", MapType(StringType(), DoubleType()), True),
    StructField("device_id", StringType(), True),
    StructField("is_fraud", BooleanType(), True)
])

# Ler stream do Kafka (usar porta 9093 para comunicação interna entre containers)
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9093") \
    .option("subscribe", "transactions_raw") \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

############################################################################ 
# Lê apenas mensagens novas (recomendado para produção em tempo real)
# .option("startingOffsets", "latest")

# # Lê todas as mensagens desde o início (útil para backfill)
# .option("startingOffsets", "earliest")
############################################################################

# Parsear JSON e adicionar metadados
parsed_df = df.select(
    from_json(col("value").cast("string"), transaction_schema).alias("data"),
    col("timestamp").alias("kafka_timestamp"),
    current_timestamp().alias("ingestion_timestamp")
).select(
    "data.*",
    "kafka_timestamp",
    "ingestion_timestamp",
    lit("kafka").alias("source")
)

# Adicionar colunas de particionamento por data
enriched_df = parsed_df \
    .withColumn("ingestion_year", year(col("ingestion_timestamp"))) \
    .withColumn("ingestion_month", month(col("ingestion_timestamp"))) \
    .withColumn("ingestion_day", dayofmonth(col("ingestion_timestamp")))

# Escrever stream para Bronze no MinIO usando Delta Lake
query = enriched_df.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", CHECKPOINT_PATH) \
    .option("path", DELTA_PATH) \
    .partitionBy("ingestion_year", "ingestion_month", "ingestion_day") \
    .trigger(processingTime="10 seconds") \
    .start()


print("✅ Bronze ingestion iniciado!")
print("📊 Processando transações do Kafka...")

# Aguardar término do stream
query.awaitTermination()