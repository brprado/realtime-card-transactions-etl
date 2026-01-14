from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
from faker import Faker
import json
import uuid
import random
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Carregar variáveis de ambiente primeiro
load_dotenv()

from Kafka.scripts.create_topic import create_kakfa_topic

fake = Faker("pt_Br")


def clean_env_value(value):
    """Remove aspas simples ou duplas do início e fim do valor"""
    if value:
        return value.strip().strip("'").strip('"')
    return value


class TransactionProducer:
    def __init__(self, bootstrap_servers=None, topic="transactions_raw"):
        # Usar valor padrão se não fornecido
        if bootstrap_servers is None:
            kafka_server = os.getenv('KAFKA_SERVER', 'localhost:9092')
            bootstrap_servers = clean_env_value(kafka_server)
        
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        
        # Tentar criar o tópico antes de criar o producer
        try:
            create_kakfa_topic(topic_name=topic)
        except Exception as e:
            print(f"⚠️  Aviso: Não foi possível criar o tópico automaticamente: {e}")
            print("   Continuando mesmo assim...")
        
        # Criar o producer com tratamento de erro
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                # converte dicionario python em uma string JSON
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                # nivel de confirmacao máximo (aguarda que o lider e todas as replicas receberam e gravaram as mensagens)
                acks="all",
                retries=3,
                compression_type="gzip",  # reduz o tamanho das mensagens
                # Permite até 5 requisições paralelas por broker sem esperar ACK
                max_in_flight_requests_per_connection=5,
                # enable_idempotence=True,  # evita duplicatas
            )
            print(f"✅ Producer conectado ao Kafka em {bootstrap_servers}")
        except NoBrokersAvailable:
            error_msg = f"""
❌ ERRO: Não foi possível conectar ao Kafka!

O Kafka não está disponível em: {bootstrap_servers}

Soluções:
1. Verifique se o Kafka está rodando:
   docker-compose up -d kafka zookeeper

2. Verifique se o Kafka está acessível:
   docker ps | grep kafka

3. Verifique a configuração no arquivo .env:
   KAFKA_SERVER=localhost:9092

4. Aguarde alguns segundos após iniciar o Kafka para ele ficar pronto
"""
            raise ConnectionError(error_msg) from None

    def generate_transactions(self, is_fraud=False):
        """
        Gera uma transação fake com possibilidade de anomalia
        """
        transaction_types = ["debit", "credit", "transfer"]
        categories = [
            "food",
            "transport",
            "entertainment",
            "utilities",
            "shopping",
            "health",
            "education",
            "bills",
            "investment",
        ]

        # transacoes normais: 10 - 500
        # transacoes fraudulentas: 1000 a 10000

        amount = round(random.uniform(1000, 10000), 2) if is_fraud else round(
            random.uniform(10, 500), 2)

        transaction = {
            "transaction_id": str(uuid.uuid4()),
            "account_id": fake.bban(),
            "transaction_type": random.choice(transaction_types),
            "amount": amount,
            "merchant": fake.company(),
            "category": random.choice(categories),
            "timestamp": datetime.now().isoformat(),
            "location": {
                "lat": float(fake.latitude()),
                "lon": float(fake.longitude())
            },
            "device_id": str(uuid.uuid4()),
            "is_fraud": is_fraud
        }

        return transaction

    def send_transaction(self, transaction):
        """Envia transação para o Kafka com callback"""
        self.producer.send(
            self.topic,
            value=transaction,
            key=transaction["account_id"].encode("utf-8")
        )

    def produce_transactions(self, rate_per_second=2, duration_minutes=5):
        """
        Produz transações continuamente
        rate_per_second: transações por segundo
        duration_minutes: duração em minutos (None = infinito)
        """
        start_time = time.time()
        count = 0

        try:
            while True:
                # 3-5% chance de fraude
                is_fraud = random.random() < 0.04

                transaction = self.generate_transactions(is_fraud=is_fraud)
                self.send_transaction(transaction)
                print(transaction['transaction_id'])
                count += 1

                if count % 100 == 0:
                    print(
                        f'Transações enviadas: {count}\nFraudes {int(count * 0.04)}')

                # contralar taxa de envio
                time.sleep(1/rate_per_second)

                # verificar duracao
                if duration_minutes and (time.time() - start_time) > (duration_minutes * 60):
                    break
        except KeyboardInterrupt:
            print(
                f'Producer interrompido. Total: {count} transacoes registradas')
        finally:
            self.producer.flush()
            self.producer.close()


if __name__ == '__main__':
    producer = TransactionProducer()
    producer.produce_transactions(rate_per_second=2)
