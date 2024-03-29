import csv
import logging
import os
import time
from io import BytesIO

import ngsi_ld_client
from kafka import KafkaConsumer
from ngsi_ld_client.api_client import ApiClient as NGSILDClient
from ngsi_ld_client.configuration import Configuration as NGSILDConfiguration
from ngsi_ld_client.exceptions import ApiException
from ngsi_ld_client.models.query_entity200_response_inner import \
    QueryEntity200ResponseInner
from pyoxigraph import Literal, parse

# Kafka information
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "containerlab")

# NGSI-LD Context Broker
BROKER_URI = os.getenv("BROKER_URI", "http://localhost:9099/ngsi-ld/v1")
DEBUG = os.getenv("DEBUG", False)

# Configure Python logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
if DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)

class PreEntity(object):

    def __init__(self, id):
        self.id = id
        self.entity_type = None
        self.attributes = {}

# Init NGSI-LD Client
configuration = NGSILDConfiguration(host=BROKER_URI)
configuration.debug = DEBUG
ngsi_ld = NGSILDClient(configuration=configuration)
api_instance = ngsi_ld_client.ContextInformationProvisionApi(ngsi_ld)

# Initialize consumer
consumer = None
while True:
    try:
        consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers=KAFKA_BROKER)
    except Exception as error:
        print("An exception occurred:", error)
        time.sleep(10)
        continue
    break

entity_cache = []
csv_file = open('/tmp/results.csv', 'a', newline='')
writer = csv.writer(csv_file)
fields = ["Subjects", "Triples", "Kafka_in", "Kafka_out","End_time"]
writer.writerow(fields)
csv_file.close()
for msg in consumer:
    # Set timestamp when message read from kafka
    kafka_out_tstamp = time.time() * 1000
    csv_file = open('/tmp/results.csv', 'a', newline='')
    writer = csv.writer(csv_file)
    logger.info("Message consumed from Kafka")
    # Get timestamp when message was written in kafka
    kafka_in_tstamp = msg.timestamp
    triples = list(parse(BytesIO(msg.value), 'application/n-quads'))
    subjects = []
    for triple in triples:
        if triple.subject in subjects:
            continue
        subjects.append(triple.subject)

    logger.info("Number of triples in RDF dataset: {0}".format(len(triples)))
    logger.info("Number of subjects in RDF dataset: {0}".format(len(subjects)))

    for subject in subjects:
        pre_entity = PreEntity(str(subject.value))
        pos= [(p,o) for s,p,o,_ in triples if s == subject]

        for p,o in pos:
            if p.value == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
                pre_entity.entity_type = ngsi_ld_client.EntityType(o.value)
            elif isinstance(o, Literal):
                prop = None
                # Special NGSI-LD representation for dateTime properties
                if o.datatype.value == "http://www.w3.org/2001/XMLSchema#DateTime":
                    prop = ngsi_ld_client.ModelProperty(
                        type="Property",
                        value=ngsi_ld_client.PropertyValue(
                            {
                                "@type": "DateTime",
                                "@value": o.value.isoformat()
                            }
                        )
                    ).to_dict()
                else:
                    prop = ngsi_ld_client.ModelProperty(
                        type="Property",
                        value=ngsi_ld_client.PropertyValue(o.value)
                    ).to_dict()
                pre_entity.attributes[p.value] = prop

            else: # Relationships then
                rel = ngsi_ld_client.Relationship(
                    type="Relationship",
                    object=o.value
                ).to_dict()
                pre_entity.attributes[p.value] = rel

        if pre_entity.id not in entity_cache:
            api_instance.create_entity(
                query_entity200_response_inner=ngsi_ld_client.QueryEntity200ResponseInner(
                    id=pre_entity.id,
                    type=pre_entity.entity_type,
                    additional_properties=pre_entity.attributes)
            )
            entity_cache.append(pre_entity.id)
            logger.info("Entity {0} created in Context Broker".format(pre_entity.id))
        else:
            api_instance.update_entity(
                entity_id=pre_entity.id,
                entity=ngsi_ld_client.Entity(
                additional_properties=pre_entity.attributes
            ))
            logger.info("Entity {0} updated in Context Broker".format(pre_entity.id))

    # Set timestamp output
    end_tstamp = time.time() * 1000
    writer.writerow([len(subjects), len(triples), kafka_in_tstamp, kafka_out_tstamp, end_tstamp])
    logger.info("Closing file")
    csv_file.close()
