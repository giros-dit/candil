import argparse
import random
import time

from kafka import KafkaProducer
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

# Namespace for example data
EX = Namespace("http://example.org/")

def generate_random_object():
    """Generate a random RDF object (URI or Literal)."""
    literal_choices = ["apple", "banana", "carrot", 123, True]
    obj_types = [
        Literal(random.choice(literal_choices)),
        URIRef(f"http://example.org/object{random.randint(0, 50)}")
    ]
    return random.choice(obj_types)

def generate_triples_message(num_subjects, triples_per_subject, class_uri):
    """
    Generate RDF triples grouped per subject.
    Each subject will always have a class triple: <subject> rdf:type <class_uri>.
    """
    g = Graph()

    subjects = [
        URIRef(f"http://example.org/subject{i}")
        for i in range(num_subjects)
    ]

    predicates = [
        URIRef(f"http://example.org/predicate{i}") for i in range(5)
    ]

    for subject in subjects:
        # Always include the rdf:type triple
        g.add((subject, RDF.type, URIRef(class_uri)))

        # Add the rest of the triples
        for _ in range(triples_per_subject):
            predicate = random.choice(predicates)
            obj = generate_random_object()
            g.add((subject, predicate, obj))

    return g.serialize(format='nt')

def send_rdf_messages(num_subjects, triples_per_subject, messages_per_second,
                      duration_seconds, kafka_bootstrap, topic, class_uri):
    """Send RDF messages to Kafka following specified rate."""
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap,
        value_serializer=lambda v: v.encode('utf-8')
    )

    interval = 1.0 / messages_per_second
    start_time = time.time()

    while time.time() - start_time < duration_seconds:
        message = generate_triples_message(num_subjects, triples_per_subject, class_uri)
        producer.send(topic, value=message)
        producer.flush()
        time.sleep(interval)

    producer.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send random RDF triples to Kafka.")
    parser.add_argument("--subjects", type=int, required=True, help="Number of subjects per message")
    parser.add_argument("--triples-per-subject", type=int, required=True, help="Number of triples per subject (EXCLUDING the rdf:type triple)")
    parser.add_argument("--mps", type=float, required=True, help="Messages per second")
    parser.add_argument("--duration", type=int, required=True, help="Test duration in seconds")
    parser.add_argument("--bootstrap", default="localhost:9092", help="Kafka bootstrap servers")
    parser.add_argument("--topic", default="rdf_triples", help="Kafka topic name")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--class-uri", default="http://example.org/SomeClass", help="URI of the class to assign to each subject")

    args = parser.parse_args()

    # Apply reproducible random seed if provided
    if args.seed is not None:
        random.seed(args.seed)

    send_rdf_messages(
        num_subjects=args.subjects,
        triples_per_subject=args.triples_per_subject,
        messages_per_second=args.mps,
        duration_seconds=args.duration,
        kafka_bootstrap=args.bootstrap,
        topic=args.topic,
        class_uri=args.class_uri
    )
