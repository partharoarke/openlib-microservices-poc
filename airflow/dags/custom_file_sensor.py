from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults
import os

class CustomFileSensor(BaseSensorOperator):
    """
    A simple sensor that waits for a file to appear at the specified absolute path.
    """
    @apply_defaults
    def __init__(self, filepath, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filepath = filepath

    def poke(self, context):
        exists = os.path.exists(self.filepath)
        self.log.info("CustomFileSensor: Checking if %s exists: %s", self.filepath, exists)
        return exists

