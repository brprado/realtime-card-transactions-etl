from kafka import KafkaProducer
from faker import Faker
import json
import uuid
import random
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv

load_dotenv()

fake = Faker("pt_Br")


class TransactionProducer:
    def __init__(self, bootstrap_servers=os.getenv('KAFKA_SERVER'), topic="transactions_raw"):
        self.topic = topic
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
            enable_idempotence=True,  # evita duplicatas
        )

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
            "device_id": uuid.uuid4(),
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
        start_time = datetime.now()
        count = 0

        try:
            while True:
                # 3-5% chance de fraude
                is_fraud = random.ramdom() < 0.04

                transaction = self.generate_transactions(is_fraud=is_fraud)
                self.send_transaction(transaction)

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
    produce.produce_transactions(rate_per_second=2)
