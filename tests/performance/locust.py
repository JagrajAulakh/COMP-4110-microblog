import pyotp

from locust import HttpUser, task, between


class PerfUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def visit_account_page(self):
        self.client.get("/user/testuser")

    def on_start(self):
        credentials = {
            "username": "testuser",
            "userid": 1,
            "password": "testuser",
            "secret": "5D2PMXTITWZHC4K5JUGGIKHOKAZJRAD2",  # Secret for testuser on production site
        }
        totp = pyotp.TOTP(credentials["secret"])

        otp_code = totp.now()

        self.client.post(
            f"/auth/login/2fa/{credentials['userid']}", data={"otp": otp_code}
        )
