import argparse
import random
import time

from kafka import KafkaProducer
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

# Namespace for example data
EX = Namespace("http://example.org/")

# Global predicate-object type map for consistency
predicate_type_map = {}

def get_or_assign_predicate_type(predicate):
    """
    Assign a fixed object type for a predicate.
    Types: 'uri', 'literal-string', 'literal-int', 'literal-bool'
    """
    if predicate not in predicate_type_map:
        if random.random() < 0.5:
            predicate_type_map[predicate] = 'uri'
        else:
            predicate_type_map[predicate] = random.choice([
                'literal-string', 'literal-int', 'literal-bool'
            ])
    return predicate_type_map[predicate]

def generate_random_subject_uri():
    """Generate a reproducible random subject URI using Python's random module."""
    # random.getrandbits allows us to generate a large random number in a reproducible way
    rand_id = random.getrandbits(64)  # 64-bit random integer
    return URIRef(f"http://example.org/subject_{rand_id}")

def generate_random_object(object_type):
    """Generate an object matching the given type."""
    if object_type == 'uri':
        return URIRef(f"http://example.org/object{random.randint(0, 50)}")

    elif object_type == 'literal-string':
        return Literal(random.choice(["apple", "banana", "carrot", "dog", "house"]), datatype=XSD.string)

    elif object_type == 'literal-int':
        return Literal(random.randint(0, 1000), datatype=XSD.integer)

    elif object_type == 'literal-bool':
        return Literal(random.choice([True, False]), datatype=XSD.boolean)

    else:
        raise ValueError(f"Unknown object type: {object_type}")

def generate_triples_message(num_subjects, total_triples, class_uri):
    g = Graph()
    subjects = [generate_random_subject_uri() for _ in range(num_subjects)]

    # Add rdf:type triple for each subject
    for subject in subjects:
        g.add((subject, RDF.type, URIRef(class_uri)))

    # Keep generating triples until we have exactly total_triples
    while len(g) < total_triples:
        subject = random.choice(subjects)
        predicate = URIRef(f"http://example.org/predicate{random.randint(0, 4)}")
        obj_type = get_or_assign_predicate_type(predicate)
        obj = generate_random_object(obj_type)
        g.add((subject, predicate, obj))  # duplicates won't increase len(g), so loop retries

    return g.serialize(format='nt')


def send_rdf_messages(num_subjects, total_triples, messages_per_second,
                      duration_seconds, kafka_bootstrap, topic, class_uri):
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap,
        value_serializer=lambda v: v.encode('utf-8')  # Only the RDF string is serialized
    )

    interval = 1.0 / messages_per_second
    start_time = time.time()

    while time.time() - start_time < duration_seconds:
        triples_data = generate_triples_message(num_subjects, total_triples, class_uri)

        # Add mps as Kafka message header (byte values required)
        producer.send(
            topic,
            value=triples_data,
            headers=[("mps", str(messages_per_second).encode("utf-8"))]
        )

        producer.flush()
        time.sleep(interval)

    producer.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send RDF triples with total triples specified per message.")
    parser.add_argument("--subjects", type=int, required=True, help="Number of subjects per message")
    parser.add_argument("--total-triples", type=int, required=True, help="Total triples per message (including rdf:type triples)")
    parser.add_argument("--mps", type=int, required=True, help="Messages per second")
    parser.add_argument("--duration", type=int, required=True, help="Test duration in seconds")
    parser.add_argument("--bootstrap", default="localhost:9092", help="Kafka bootstrap servers")
    parser.add_argument("--topic", default="rdf_triples", help="Kafka topic name")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--class-uri", default="http://example.org/SomeClass", help="URI of the class assigned to each subject")

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    send_rdf_messages(
        num_subjects=args.subjects,
        total_triples=args.total_triples,
        messages_per_second=args.mps,
        duration_seconds=args.duration,
        kafka_bootstrap=args.bootstrap,
        topic=args.topic,
        class_uri=args.class_uri
    )
