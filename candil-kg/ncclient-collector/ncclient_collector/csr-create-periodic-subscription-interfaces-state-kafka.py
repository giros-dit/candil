import sys
import time

from kafka import KafkaProducer
from ncclient import manager
from ncclient.xml_ import to_ele

if len(sys.argv) < 4:
    print("Error - Incorrect arguments")
    print('Usage: python3 csr-create-periodic-subscription-interfaces-state-kafka.py <container_name> <interface_name> <period_in_cs>')
    print('Example: python3 csr-create-periodic-subscription-interfaces-state-kafka.py clab-telemetry-testbed-r1 GigabitEthernet1 1000')
    exit(1)
else:
    container_name = sys.argv[1]

r = {
    "host": container_name,
    "port": 830,
    "username": "admin",
    "password": "admin",
    "hostkey_verify": False,
    "device_params": {"name": "csr"}
}

print(container_name)

while True:
    print("Connecting to kafka")
    try:
        producer = KafkaProducer(bootstrap_servers=['kafka:9092'])
    except Exception as error:
        print("An exception occurred:", error)
        time.sleep(5)
        continue
    break

while True:
    print("Connecting to NETCONF server")
    try:
        session = manager.connect(**r)
    except Exception as error:
        print("An exception occurred:", error)
        time.sleep(5)
        continue
    break

print ("\nSession ID: ", session.session_id)

xpath = "/interfaces-state/interface[name=\'" + sys.argv[2] + "\']"
subscription = "period"
period = sys.argv[3]


# When building the RPC request XML, use dampening-period for on-change notifications (when supported).
# Otherwise, use period and specify an integer value for the time in centiseconds.

rpc = """

    <establish-subscription xmlns="urn:ietf:params:xml:ns:yang:ietf-event-notifications"
    xmlns:yp="urn:ietf:params:xml:ns:yang:ietf-yang-push">
        <stream>yp:yang-push</stream>
        <yp:xpath-filter>{0}</yp:xpath-filter>
        <yp:{1}>{2}</yp:{1}>
    </establish-subscription>

""".format(xpath, subscription, period)

request = session.dispatch(to_ele(rpc))

print(request)

print("\nYANG-Push notifications for XPath " + xpath + " of network device "+ container_name + ": \n")

while True:
    sub_data = session.take_notification()
    print(str(sub_data.notification_xml).encode('utf-8'))
    if (sub_data != None):
        producer.send('yang-push', value=str(sub_data.notification_xml).encode('utf-8'))
    producer.flush()
