import json
import logging
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient


def create_mqtt_client(host, ca_file, private_file, cert_file, thing_name):
    client = AWSIoTMQTTClient(thing_name)
    client.configureCredentials(ca_file, private_file, cert_file)
    client.configureEndpoint(host, 8883)
    client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    client.configureDrainingFrequency(2)  # Draining: 2 Hz
    client.configureConnectDisconnectTimeout(10)  # 10 sec
    client.configureMQTTOperationTimeout(5)  # 5 sec
    return client


class AwsDataPublisher:
    def __init__(self, mqtt_client, thing_name, topic_prefix):
        self._client = mqtt_client
        self._thing_name = thing_name
        self._topic_prefix = topic_prefix
        self._client.connect()
        self._log = logging.getLogger(__name__)

    def publish_data(self, payload):
        self._log.info("Published " + self._thing_name + " data to AWS")
        self._log.debug(payload)
        self._client.publish("/".join([self._topic_prefix, self._thing_name]), json.dumps(payload), 1)


