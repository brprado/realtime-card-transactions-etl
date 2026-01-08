from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
from dotenv import load_dotenv
import os

load_dotenv()


def create_kakfa_topic(
    topic_name="transactions_raw", num_partitions=3, replication_factor=1
):
    """Cria tópico no kafka programaticamente"""

    admin_client = KafkaAdminClient(
        bootstrap_servers=os.getenv("KAFKA_SERVER"), client_id="topic-creator"
    )

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
