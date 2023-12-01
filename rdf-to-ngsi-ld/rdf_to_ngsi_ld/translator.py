import os
from io import BytesIO

import ngsi_ld_client
from kafka import KafkaConsumer
from ngsi_ld_client.api_client import ApiClient as NGSILDClient
from ngsi_ld_client.configuration import Configuration as NGSILDConfiguration
from ngsi_ld_client.exceptions import ApiException
from ngsi_ld_client.models.query_entity200_response_inner import \
    QueryEntity200ResponseInner
from pyoxigraph import Literal, parse


class PreEntity(object):

    def __init__(self, id):
        self.id = id
        self.entity_type = None
        self.attributes = {}

# Kafka information
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "containerlab")

# NGSI-LD Context Broker
BROKER_URI = os.getenv("BROKER_URI", "http://localhost:9099/ngsi-ld/v1")
DEBUG = os.getenv("DEBUG", True)

# Init NGSI-LD Client
configuration = NGSILDConfiguration(host=BROKER_URI)
configuration.debug = DEBUG
ngsi_ld = NGSILDClient(configuration=configuration)
api_instance = ngsi_ld_client.ContextInformationProvisionApi(ngsi_ld)

# Initialize consumer
disconnected = True
consumer = None
while disconnected:
    try:
        consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers=KAFKA_BROKER)
    except:
        continue
    disconnected = False

entity_cache = []
for msg in consumer:
    subjects = []

    triples = list(parse(BytesIO(msg.value), 'application/n-quads'))

    subjects = []
    for triple in triples:
        if triple.subject in subjects:
            continue
        subjects.append(triple.subject)

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
        else:
            import pdb; pdb.set_trace()
            api_instance.update_entity(entity_id=pre_entity.id, entity=ngsi_ld_client.Entity(
                additional_properties=pre_entity.attributes
            ))
