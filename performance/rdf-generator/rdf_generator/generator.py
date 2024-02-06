import io
import logging
import os
import socket
import time

from kafka import KafkaProducer
from pyoxigraph import Literal, NamedNode, Quad, Store

# Kafka information
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "rdf-streams")

# RDF generator
ENTITIES = os.getenv("ENTITIES", [1, 2, 5, 10, 50, 100, 200, 500, 1000, 2000, 5000])

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

while True:
    print("Connecting to kafka in URL {0}".format(KAFKA_BROKER) )
    try:
        producer = KafkaProducer(bootstrap_servers=[KAFKA_BROKER])
    except Exception as error:
        print("An exception occurred:", error)
        time.sleep(5)
        continue
    break

for experiment in range(100):
    logger.info("Starting experiment {0}".format(experiment))
    round = 0
    for amount in ENTITIES:
        store = Store()
        for n in range(amount):
            subject = NamedNode("http://example.com#round{0}-entity{1}".format(round, n))
            # Build "rdf:type" triple
            store.add(Quad(
                subject,
                NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                NamedNode("http://example.com#DummyEntity")
            ))
            store.add(Quad(
                subject,
                NamedNode("http://example.com#name"),
                Literal("entity-{0}".format(n))
            ))
        output = io.BytesIO()
        store.dump(output,"application/n-triples")

        logger.info("Sending round {0} of RDF data to Kafka".format(round))

        producer.send(KAFKA_TOPIC, value=output.getvalue())
        producer.flush()

        time.sleep(2)
        round += 1

    experiment += 1

