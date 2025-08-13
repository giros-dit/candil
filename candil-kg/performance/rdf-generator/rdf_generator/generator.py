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
            # URI object type
            predicate_type_map[predicate] = 'uri'
        else:
            # Literal object type -> choose *one* literal datatype
            literal_type = random.choice(['literal-string', 'literal-int', 'literal-bool'])
            predicate_type_map[predicate] = literal_type
    return predicate_type_map[predicate]

def generate_random_object(object_type):
    """Generate an object matching the given type."""
    if object_type == 'uri':
        return URIRef(f"http://example.org/object{random.randint(0, 50)}")

    elif object_type == 'literal-string':
        choices = ["apple", "banana", "carrot", "dog", "house"]
        return Literal(random.choice(choices), datatype=XSD.string)

    elif object_type == 'literal-int':
        return Literal(random.randint(0, 1000), datatype=XSD.integer)

    elif object_type == 'literal-bool':
        return Literal(random.choice([True, False]), datatype=XSD.boolean)

    else:
        raise ValueError(f"Unknown object type: {object_type}")

def generate_triples_message(num_subjects, triples_per_subject, class_uri):
    """
    Generate triples with:
    - Consistent URI or literal type per predicate
    - If literal, consistent literal datatype across run for that predicate
    """
    g = Graph()
    subjects = [URIRef(f"http://example.org/subject{i}") for i in range(num_subjects)]

    for subject in subjects:
        # Always add rdf:type triple
        g.add((subject, RDF.type, URIRef(class_uri)))

        for _ in range(triples_per_subject):
            predicate = URIRef(f"http://example.org/predicate{random.randint(0, 4)}")
            obj_type = get_or_assign_predicate_type(predicate)
            obj = generate_random_object(obj_type)
            g.add((subject, predicate, obj))

    return g.serialize(format='nt')

def send_rdf_messages(num_subjects, triples_per_subject, messages_per_second,
                      duration_seconds, kafka_bootstrap, topic, class_uri):
    """
    Send triples to Kafka with consistent predicate object and literal datatype types.
    """
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap,
        value_serializer=lambda v: v.encode('utf-8')
    )

    interval = 1.0 / messages_per_second
    start_time = time.time()

    while time.time() - start_time < duration_seconds:
        triples_data = generate_triples_message(num_subjects, triples_per_subject, class_uri)
        producer.send(topic, value=triples_data)
        producer.flush()
        time.sleep(interval)

    producer.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send RDF triples with consistent predicate-object types and literal datatypes to Kafka.")
    parser.add_argument("--subjects", type=int, required=True, help="Number of subjects per message")
    parser.add_argument("--triples-per-subject", type=int, required=True, help="Triples per subject (excluding rdf:type)")
    parser.add_argument("--mps", type=float, required=True, help="Messages per second")
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
        triples_per_subject=args.triples_per_subject,
        messages_per_second=args.mps,
        duration_seconds=args.duration,
        kafka_bootstrap=args.bootstrap,
        topic=args.topic,
        class_uri=args.class_uri
    )
