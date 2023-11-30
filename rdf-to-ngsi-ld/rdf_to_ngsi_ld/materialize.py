import ngsi_ld_client
import rdflib
from kafka import KafkaConsumer
from ngsi_ld_client.api_client import ApiClient

subjects = []
entity_cache = []

class PreEntity(object):

    def __init__(self, id):
        self.id = id
        self.entity_type = None
        self.attributes = {}

#kakfa_consumer = KafkaConsumer(broker, port, topic)
#kafka_consumer.receive(): DO BELOW when processed
#graph = rdflib.Graph()
#graph.parse(kafka_event)

for s in graph.subjects():
    if s not in subjects:
        pre_entity = PreEntity(str(s))
        pos = graph.predicate_objects(subject=s)
        for p,o in pos:
            if p == rdflib.RDF.type:
                pre_entity.entity_type = ngsi_ld_client.EntityType(str(o))
            elif isinstance(o, rdflib.Literal):
                prop = None
                # Special NGSI-LD representation for dateTime properties
                if o.datatype == rdflib.XSD.dateTime:
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
                pre_entity.attributes[str(p)] = prop

            else: # Relationships then
                rel = ngsi_ld_client.Relationship(
                    type="Relationship",
                    object=str(o)
                ).to_dict()
                pre_entity.attributes[str(p)] = rel

        entity = ngsi_ld_client.Entity(
            id=pre_entity.id,
            type=pre_entity.entity_type,
            additional_properties=pre_entity.attributes
        )
        print(entity.to_json())

        #if entity.id in entity_cache:
            # ngsi_ld_client.update_entity(entity_id)
        #else:
            # ngsi_ld_client.create_entity

        subjects.append(s)
        #entity_cache.append(entity.id)
