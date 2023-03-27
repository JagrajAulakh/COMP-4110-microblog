import time

from locust import HttpUser, task, between

class PerfUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def visit_account_page(self):
        self.client.get("/auth/login")


    def on_start(self):
        # self.client.post("/login", json={"username":"foo", "password":"bar"})
        pass


