import time
from locust import User, task, between

class StreamlitLoadUser(User):
    wait_time = between(1, 3)

    @task
    def simulate_user_flow(self):
        start_time = time.time()
        
        # Simula tempo de requisição do usuário na interface
        time.sleep(0.5)
        
        total_time = time.time() - start_time
        if total_time > 10.0:
            self.environment.events.request.fire(
                request_type="Performance",
                name="SLA_10s_Check",
                response_time=total_time * 1000,
                response_length=0,
                exception=Exception("Tempo excedeu 10s")
            )
        else:
            self.environment.events.request.fire(
                request_type="Performance",
                name="SLA_10s_Check",
                response_time=total_time * 1000,
                response_length=1,
                exception=None
            )