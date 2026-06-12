from locust import HttpUser, task, between
import json

class OmniCoreUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        self.token = "LEARNING_test_agent_001"
        self.headers = {"Authorization": self.token}

    @task
    def call_command(self):
        payload = {
            "command": "stock.get_all",
            "params": {}
        }
        self.client.post(
            "/api/command", 
            json=payload, 
            headers=self.headers,
            name="Execute Command"
        )

if __name__ == "__main__":
    # This allows running the file directly for debugging
    print("Locust file loaded.")
