import logging
import os
import subprocess
import time
from datetime import datetime

import requests

# Configuration
HEARTBEAT_URL = os.getenv(
    "OMNICORE_HEARTBEAT_URL", "http://localhost:8000/api/heartbeat"
)
# Use a generic restart script name that the system will expect
RESTART_COMMAND = os.getenv(
    "OMNICORE_RESTART_CMD",
    "bash /home/adrian/Escritorio/repo/system_ops/restart_motor.sh",
)
CHECK_INTERVAL = 5  # Seconds
FAILURE_THRESHOLD = 3

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] SENTINEL: %(message)s"
)
logger = logging.getLogger("OmniCore.Sentinel")


class OmniSentinel:
    """
    External Watchdog for OmniCore-AI.
    Implements the Sentinel Pattern: Monitoring, Health Validation, and Auto-Recovery.
    """

    def __init__(self):
        self.failures = 0
        self.last_restart = None
        logger.info(f"Sentinel initialized. Monitoring {HEARTBEAT_URL}")

    def check_health(self) -> bool:
        """
        Validates system health via the heartbeat endpoint.
        Returns True if the motor is responsive and healthy.
        """
        try:
            response = requests.get(HEARTBEAT_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Basic sanity check of the heartbeat payload
                if data.get("status") == "ALIVE":
                    return True
                logger.warning(f"Heartbeat payload invalid: {data}")
            else:
                logger.warning(f"Heartbeat returned status: {response.status_code}")
        except Exception as e:
            logger.error(f"Heartbeat request failed: {e}")
        return False

    def restart_motor(self):
        """
        Triggers the system restart sequence.
        Ensures the motor is brought back online after a critical failure.
        """
        logger.critical(
            "🚨 CRITICAL: Heartbeat lost! Initiating emergency recovery sequence..."
        )
        try:
            # Execute the restart command
            result = subprocess.run(
                RESTART_COMMAND, shell=True, check=True, capture_output=True, text=True
            )
            logger.info(f"Recovery command executed: {result.stdout}")
            self.last_restart = datetime.now()
        except subprocess.CalledProcessError as e:
            logger.error(f"Recovery sequence failed: {e.stderr}")

    def run(self):
        """
        Main monitoring loop.
        Implements the failure threshold logic to avoid premature restarts during boot.
        """
        while True:
            if self.check_health():
                if self.failures > 0:
                    logger.info("✅ System recovered. Resetting failure counter.")
                self.failures = 0
            else:
                self.failures += 1
                logger.warning(
                    f"⚠️ Health check failure ({self.failures}/{FAILURE_THRESHOLD})"
                )

                if self.failures >= FAILURE_THRESHOLD:
                    self.restart_motor()
                    # Reset failures and wait longer to allow the system to boot
                    self.failures = 0
                    logger.info("Waiting 30s for system boot-up...")
                    time.sleep(30)

            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    sentinel = OmniSentinel()
    try:
        sentinel.run()
    except KeyboardInterrupt:
        logger.info("Sentinel stopped by administrator.")
