import logging
import os
import subprocess
import time

import requests

# Configuration
HEARTBEAT_URL = os.getenv(
    "OMNICORE_HEARTBEAT_URL", "http://localhost:8000/api/heartbeat"
)
RESTART_COMMAND = "/home/adrian/Escritorio/railway/OmniCore-AI/restart_backend.sh"
# In production, this would be a systemctl restart or a Kubernetes pod deletion
CHECK_INTERVAL = 2  # Seconds
FAILURE_THRESHOLD = 2

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] SENTINEL: %(message)s"
)
logger = logging.getLogger("OmniCore.Sentinel")


class OmniSentinel:
    """
    External Watchdog for OmniCore-AI.
    Ensures the motor stays alive by monitoring the heartbeat and triggering auto-restarts.
    """

    def __init__(self):
        self.failures = 0
        logger.info(f"Sentinel initialized. Monitoring {HEARTBEAT_URL}")

    def check_health(self) -> bool:
        """Checks the heartbeat endpoint."""
        try:
            response = requests.get(HEARTBEAT_URL, timeout=5)
            if response.status_code == 200:
                return True
            logger.warning(f"Heartbeat returned non-200 status: {response.status_code}")
        except Exception as e:
            logger.error(f"Heartbeat request failed: {e}")
        return False

    def restart_motor(self):
        """Triggers the system restart command."""
        logger.critical(
            "🚨 Heartbeat lost! Triggering emergency restart of OmniCore-AI..."
        )
        try:
            # Execute the restart command
            result = subprocess.run(
                RESTART_COMMAND, shell=True, check=True, capture_output=True
            )
            logger.info(
                f"Restart command executed successfully: {result.stdout.decode()}"
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart motor: {e.stderr.decode()}")

    def run(self):
        """Main monitoring loop."""
        while True:
            if self.check_health():
                if self.failures > 0:
                    logger.info("✅ Motor recovered. Resetting failure counter.")
                self.failures = 0
            else:
                self.failures += 1
                logger.warning(
                    f"⚠️ Heartbeat failure detected ({self.failures}/{FAILURE_THRESHOLD})"
                )

                if self.failures >= FAILURE_THRESHOLD:
                    self.restart_motor()
                    self.failures = 0  # Reset after restart to allow boot time

            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    sentinel = OmniSentinel()
    try:
        sentinel.run()
    except KeyboardInterrupt:
        logger.info("Sentinel stopped by user.")
