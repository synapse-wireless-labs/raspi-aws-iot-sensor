import datetime
import logging
import os.path
import time

from aws_device_config import AwsDeviceConfig, create_shadow_client
from aws_data_publisher import AwsDataPublisher, create_mqtt_client
from data_collector import create_collector

# external requirements
ROOT_CA_FILE = os.path.expanduser("~/rootCA.crt")
CERT_FILE = os.path.expanduser("~/cert.pem")
PRIVATE_FILE = os.path.expanduser("~/private.key")
HOST = os.environ['AWS_IOT_HOST']
TOPIC_PREFIX = os.environ['AWS_IOT_TOPIC_PREFIX']

# constants
ONE_SECOND = datetime.timedelta(seconds=1)

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gather_data")


def get_aws_config(thing_name):
    shadow_client = create_shadow_client(HOST, ROOT_CA_FILE, PRIVATE_FILE, CERT_FILE, thing_name)
    config = AwsDeviceConfig(aws_shadow_client=shadow_client, thing_name=thing_name)

    # retrieve sensor list from AWS
    logger.info("Retrieving sensor list from AWS...")
    sensor_config = config.get_sensor_list()
    num_sensors = len(sensor_config)
    logger.info("Found " + str(num_sensors) + " sensor" + ("" if num_sensors == 1 else "s"))

    return sensor_config


def create_publisher(thing_name):
    mqtt_client = create_mqtt_client(HOST, ROOT_CA_FILE, PRIVATE_FILE, CERT_FILE, thing_name)
    return AwsDataPublisher(mqtt_client=mqtt_client, thing_name=thing_name, topic_prefix=TOPIC_PREFIX)


def main(thing_name):
    # retrieve sensor list from AWS
    sensor_config = get_aws_config(thing_name)

    # create data collector
    collector = create_collector(sensor_config)

    # create data publisher
    publisher = create_publisher(thing_name)

    logger.info("Starting to gather data from sensors")

    while True:
        t1 = datetime.datetime.now()

        # stores readings from all configured sensors
        logger.debug("Reading sensors")
        collector.read_all_sensors()

        # publish readings if collector is full
        if collector.is_full():
            map(lambda p: publisher.publish_data(p), collector.get_sensor_payload_list())
            collector.reset()

        elapsed_time = (datetime.datetime.now() - t1)
        sleep_time = ONE_SECOND - elapsed_time if ONE_SECOND > elapsed_time else 0
        time.sleep(sleep_time.total_seconds())


if __name__ == "__main__":
    # get Raspberry Pi MAC address from end of serial number
    mac_addr = "ffffff"
    with open("/proc/cpuinfo", "r") as f:
        for line in f.readlines():
            if line[0:6] == "Serial":
                mac_addr = line[20:26]

    main(mac_addr)


