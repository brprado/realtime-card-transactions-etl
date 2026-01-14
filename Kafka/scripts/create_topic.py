from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
from dotenv import load_dotenv
import os

load_dotenv()


def clean_env_value(value):
    """Remove aspas simples ou duplas do início e fim do valor"""
    if value:
        return value.strip().strip("'").strip('"')
    return value


def create_kakfa_topic(
    topic_name="transactions_raw", num_partitions=3, replication_factor=1, bootstrap_servers=None
):
    """Cria tópico no kafka programaticamente"""
    
    # Usar valor padrão se não fornecido
    if bootstrap_servers is None:
        kafka_server = os.getenv("KAFKA_SERVER", "localhost:9092")
        bootstrap_servers = clean_env_value(kafka_server)

    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=bootstrap_servers, client_id="topic-creator"
        )
    except NoBrokersAvailable:
        error_msg = f"""
❌ ERRO: Não foi possível conectar ao Kafka para criar o tópico!

O Kafka não está disponível em: {bootstrap_servers}

Soluções:
1. Verifique se o Kafka está rodando:
   docker-compose up -d kafka zookeeper

2. Verifique se o Kafka está acessível:
   docker ps | grep kafka

3. Aguarde alguns segundos após iniciar o Kafka para ele ficar pronto
"""
        raise ConnectionError(error_msg) from None

    existing_topics = admin_client.list_topics()

    if topic_name in existing_topics:
        print(f"O topico {topic_name} já existe")
        return

    topic_list = [
        NewTopic(
            name=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
        )
    ]

    try:
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        print(f"Tópico '{topic_name}' criado com sucesso!")
        print(f"- Partições: {num_partitions}")
        print(f"- Replication Factor: {replication_factor}")
    except TopicAlreadyExistsError:
        print(f'O topico {topic_name} já existe')
    finally:
        admin_client.close()


if __name__ == "__main__":
    create_kakfa_topic()
