import time
import datetime
from spi_sensor import SpiSensor


def create_collector(sensor_config):
    def create_spi_sensor_data(channel, config):
        sensor = SpiSensor(channel=channel,
                           name=(config.get("name", "error")),
                           type_str=(config.get("type", "error")),
                           description=(config.get("description", None)),
                           avg_length=(config.get("avg_length", 0)),
                           offset=(config.get("cal_offset", 0)),
                           max_value=(config.get("sensor_max", 0)))

        return DataCollector.SensorData(sensor)

    # create list of SpiSensors
    sensor_data_objects = [create_spi_sensor_data(c, s) for c, s in enumerate(sensor_config)]

    # return new object
    return DataCollector(sensor_data_objects)


class DataCollector:
    class SensorData:
        def __init__(self, sensor):
            self._values = []
            self._sensor = sensor
            self._start_time = 0

        def store_sensor_value(self):
            if not self._values:
                self._start_time = time.mktime(datetime.datetime.now().timetuple())

            # Save latest reading
            self._values.append(self._sensor.get_sensor_reading())

        def reset(self):
            del self._values[:]

        def get_payload(self):
            return {'timestamp': self._start_time,
                    'values': self._values,
                    'sensor': self._sensor.get_sensor_name(),
                    'type': self._sensor.get_sensor_type(),
                    'description': self._sensor.get_sensor_description()
                    }

    def __init__(self, sensor_data_list=None, max_readings_per_sensor=60):
        self._sensors = []
        self._readings = 0
        self._max_values = max_readings_per_sensor

        if isinstance(sensor_data_list, list):
            self._sensors = sensor_data_list

    def is_full(self):
        return self._readings >= self._max_values

    def read_all_sensors(self):
        self._readings += 1
        map(lambda s: s.store_sensor_value(), self._sensors)

    def reset(self):
        map(lambda s: s.reset(), self._sensors)
        self._readings = 0

    def get_sensor_payload_list(self):
        return [s.get_payload() for s in self._sensors]