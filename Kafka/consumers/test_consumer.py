from kafka import KafkaConsumer
from dotenv import load_dotenv
import os
import json
import signal
import sys

load_dotenv()


def clean_env_value(value):
    """Remove aspas simples ou duplas do início e fim do valor"""
    if value:
        return value.strip().strip("'").strip('"')
    return value


class RealtimeTransactionConsumer:
    def __init__(self, topic='transactions_raw'):
        self.topic = topic
        self.running = True
        
        # Obter e limpar o valor do KAFKA_SERVER
        kafka_server = os.getenv('KAFKA_SERVER', 'localhost:9092')
        bootstrap_servers = clean_env_value(kafka_server)
        
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset='latest',  # Começa das mensagens novas
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='transaction-consumer-group',  # Grupo para rastrear offset
            enable_auto_commit=False,  # Commit automático do offset
            # Removido consumer_timeout_ms para rodar infinitamente
        )

        # Handler para shutdown gracioso
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        self.count = 0
        self.fraud_count = 0

    def shutdown(self, signum, frame):
        """Shutdown gracioso quando receber Ctrl+C"""
        print(f"\n\n{'='*60}")
        print("🛑 Encerrando consumer...")
        print(f"Total processado: {self.count} transações")
        print(
            f"Fraudes detectadas: {self.fraud_count} ({(self.fraud_count/self.count*100):.1f}%)")
        print(f"{'='*60}\n")

        self.running = False
        self.consumer.close()
        sys.exit(0)

    def process_transaction(self, transaction):
        """Processa cada transação individualmente"""
        self.count += 1

        if transaction.get('is_fraud'):
            self.fraud_count += 1

        print(f"\n{'='*60}")
        print(f"📊 Transação #{self.count}")
        print(f"{'='*60}")
        print(f"🆔 Transaction ID: {transaction['transaction_id']}")
        print(f"👤 Account: {transaction['account_id']}")
        print(f"💳 Type: {transaction['transaction_type']}")
        print(f"💰 Amount: R$ {transaction['amount']:.2f}")
        print(f"🏪 Merchant: {transaction['merchant']}")
        print(f"📂 Category: {transaction['category']}")
        print(f"🕐 Timestamp: {transaction['timestamp']}")

        if transaction.get('is_fraud'):
            print(f"⚠️  FRAUDE DETECTADA!")

        print(f"{'='*60}")

    def start_consuming(self):
        """Inicia consumo contínuo em real-time"""
        print(f"\n🚀 Consumer iniciado!")
        print(f"📡 Aguardando mensagens do tópico '{self.topic}'...")
        print(f"💡 Pressione Ctrl+C para encerrar\n")

        try:
            # Loop infinito - processa mensagens conforme chegam
            for message in self.consumer:
                if not self.running:
                    break

                transaction = message.value
                self.process_transaction(transaction)
                self.consumer.commit()

        except KeyboardInterrupt:
            self.shutdown(None, None)
        except Exception as e:
            print(f"\n❌ Erro no consumer: {e}")
        finally:
            if self.consumer:
                self.consumer.close()


if __name__ == '__main__':
    consumer = RealtimeTransactionConsumer()
    consumer.start_consuming()
