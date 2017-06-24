import json
import time
import logging

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient


def create_shadow_client(host, ca_file, private_file, cert_file, thing_name):
    client = AWSIoTMQTTShadowClient(thing_name)
    client.configureCredentials(ca_file, private_file, cert_file)
    client.configureEndpoint(host, 8883)
    client.configureConnectDisconnectTimeout(10)  # 10 sec
    client.configureMQTTOperationTimeout(5)  # 5 sec
    return client


class AwsDeviceConfig:
    def __init__(self, aws_shadow_client, thing_name):
        self._complete_tokens = {}
        self._log = logging.getLogger(__name__)

        aws_shadow_client.connect()
        self._thing_shadow = aws_shadow_client.createShadowHandlerWithName(thing_name, True)
        self._thing_shadow.shadowRegisterDeltaCallback(self._shadow_delta_callback)

        # THIS IS IMPORTANT FOR SOME REASON
        time.sleep(2)

    def _shadow_delta_callback(self, response_status, token):
        self._log.debug("Received a delta message")

    def update_config(self, reported):
        token = self._thing_shadow.shadowUpdate(reported, self._shadow_update_callback, 5)
        return self._wait_on_callback(token)

    def _shadow_update_callback(self, payload, response_status, token):
        result = []

        if response_status == "accepted":
            self._log.info("Updated AWS with current config")
            state = json.loads(payload).get("state", {})
            reported = state.get("reported", {})
            result = reported.get("sensors", result)
        else:
            self._log.debug("Delete request " + token + " " + response_status)
            self._log.debug(payload)

        self._complete_tokens[token] = result

    def get_sensor_list(self):
        token = self._thing_shadow.shadowGet(self._shadow_get_callback, 5)
        return self._wait_on_callback(token)

    def _wait_on_callback(self, token):
        while token not in self._complete_tokens:
            time.sleep(.1)

        return self._complete_tokens.pop(token)

    def _shadow_get_callback(self, payload, response_status, token):
        result = []

        if response_status == "accepted":
            self._log.info("Retrieved config from AWS")

            state = json.loads(payload).get("state", {})
            desired = state.get("desired", {})
            result = desired.get("sensors", result)

            # Update shadow to report what was requested
            self.update_config(json.dumps({"state": {"reported": desired}}))

        else:
            self._log.debug("Delete request " + token + " " + response_status)
            self._log.debug(payload)

        self._complete_tokens[token] = result

