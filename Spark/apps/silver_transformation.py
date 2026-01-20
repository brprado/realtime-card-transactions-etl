from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, lit, hour, dayofweek, 
    lag, unix_timestamp, broadcast
)
from pyspark.sql.window import Window
from delta.tables import DeltaTable
import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Configurações MinIO
MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"

BRONZE_BUCKET = "bronze"
SILVER_BUCKET = "silver"

BRONZE_PATH = f"s3a://{BRONZE_BUCKET}/transactions"
SILVER_PATH = f"s3a://{SILVER_BUCKET}/transactions_cleaned"
CHECKPOINT_PATH = f"s3a://{SILVER_BUCKET}/checkpoints/silver"

# Criar SparkSession
spark = SparkSession.builder \
    .appName("SilverTransformation") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Configurar MinIO
hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
hadoop_conf.set("fs.s3a.endpoint", f"http://{MINIO_ENDPOINT}")
hadoop_conf.set("fs.s3a.access.key", MINIO_ACCESS_KEY)
hadoop_conf.set("fs.s3a.secret.key", MINIO_SECRET_KEY)
hadoop_conf.set("fs.s3a.path.style.access", "true")
hadoop_conf.set("fs.s3a.connection.ssl.enabled", "false")
hadoop_conf.set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
hadoop_conf.set("fs.s3a.aws.credentials.provider", 
                "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")

print("🔄 Iniciando processamento Silver...")

bronze_df = spark.readStream \
    .format('delta') \
    .option('ignoreDeletes','true') \
    .option('ignoreChanges','true') \
    .load(BRONZE_PATH)

print('Conectado ao data lake bronze')

validated_df = bronze_df.filter