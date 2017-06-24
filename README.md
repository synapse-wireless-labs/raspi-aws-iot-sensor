# raspi-aws-iot-sensor
Raspberry Pi 3 sensor reporting via AWS IoT

# Local requirements 

- AWS credentials located in home directory:
  - ``~/rootCA.crt``
  - ``~/cert.pem``
  - ``~/private.key``
- Environment variables set:
  - ``AWS_IOT_HOST``
    - ex. ``<server-id>.iot.<region>.amazonaws.com``
  - ``TOPIC_PREFIX``
    - ex. ``company/sensor/data/``

# Installation
``pip install -r requirements.txt``

# Start Data Collection
``python src/gather_data.py``