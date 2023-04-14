import pytest
from config import Config
from app import create_app, db
from app.models import User
from flask_login import login_user, current_user
from pytest_mock import mocker
import flask_login
import pyotp


auth_login_url = "/auth/login"
auth_register_url = "/auth/register"

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    ELASTICSEARCH_URL = None
    WTF_CSRF_ENABLED = False


class TestAuthRoutes:
    @pytest.fixture(autouse=True)
    def client(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_test_request_context = self.app.test_request_context()
        self.app_test_request_context.push()
        self.app_context.push()
        db.create_all()
        yield self.app.test_client()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @pytest.fixture()
    def create_user(self, secret):
        u1 = User(username="john", email="john@example.com")
        u1.set_two_FA(secret)
        u1.set_password("batata")
        db.session.add(u1)
        db.session.commit()
        return u1

    @pytest.fixture()
    def secret(self):
        return "gabagoo"

    def test_two_fa_hopt(self):
        import pyotp
        import time
        secret = pyotp.random_base32()

        totp = pyotp.TOTP(secret)

        code = totp.now()

        assert totp.verify(code)

        assert not totp.verify('123456')

        next_time = int(time.time()) + 30
        next_code = totp.at(next_time)
        
        assert code != next_code

    def test_login_get(self, client, create_user):
        resp = client.get(auth_login_url)
        assert resp.status_code == 200
        assert b"Sign In" in resp.data
        assert b"Register" in resp.data

    def test_login_invalid_password(self, client, create_user):
        resp = client.post(
            auth_login_url,
            data={
                "username": create_user.username,
                "password": "lala",
            },
        )
        assert resp.status_code == 302
        assert auth_login_url in resp.headers.get("Location")

    def test_login_valid_user(self, client, create_user):
        yotp =  pyotp.TOTP(create_user.fa_token)
        resp = client.post(
            f"/auth/login/2fa/{create_user.id}",
             data={
                "otp": yotp.now()
             },
        )
        assert resp.status_code == 302
        assert "index" in resp.headers.get("Location")

    def test_login_twice(self, client, create_user):
        yotp =  pyotp.TOTP(create_user.fa_token)
        resp = client.post(
            f"/auth/login/2fa/{create_user.id}",
             data={
                "otp": yotp.now()
             },
        )
        assert resp.status_code == 302
        assert "index" in resp.headers.get("Location")

    def test_login_invalid_username(self, client):
        resp = client.post(
            auth_login_url,
            data={
                "username": "jagraj3",
                "password": "batata",
            },
        )
        assert resp.status_code == 302
        assert auth_login_url in resp.headers.get("Location")


    def test_logout(self, client, create_user):
        resp = client.get("/auth/logout")
        assert resp.status_code == 302
        assert "index" in resp.headers.get("Location")


    def test_register_get(self, client):
    	resp = client.get(auth_register_url)
    	assert resp.status_code == 200


    def test_register_create_user(self, client):
        resp = client.post(
            auth_register_url,
            data={
                "username": "wannabe",
                "email": "wannabe@gmail.com",
                "password": "batata",
                "password2": "batata",
            },
        )
        assert resp.status_code == 200

    def test_register_redirect(self, mocker, client, create_user):
        resp = client.post(
            auth_register_url,
            data={
                "username": create_user.username,
                "email": create_user.email,
                "password": "batata",
                "password2": "batata",
            },)
        assert resp.status_code == 200

    def test_reset_password(self, client, create_user):
        resp = client.post(
            "/auth/reset_password_request",
            data={
                "email": create_user.email
            },)
        assert resp.status_code == 302


    def test_invalid_2fa_token(self, client, create_user):
        yotp =  pyotp.TOTP(create_user.fa_token)
        resp = client.post(
            f"/auth/login/2fa/{create_user.id}",
             data={
                "otp": "asfij1421341"
             },
        )
        assert resp.status_code == 302
        assert "2fa" in resp.headers.get("Location")


    def test_2fa_redirect(self, client, create_user):
        resp = client.post(
            auth_login_url,
            data={
                "username": create_user.username,
                "password": "batata",
            },)
        assert resp.status_code == 302
        assert "/2fa" in resp.headers.get("Location")

    def test_reset_password_token(self, client, create_user):
        token = create_user.get_reset_password_token()
        resp = client.post(
            f"/auth/reset_password/{token}", data={"password": "monkey", "password2": "monkey"})
        assert resp.status_code == 302
        assert create_user.check_password("monkey")
        assert "/login" in resp.headers.get("Location")



    def test_reset_password_token_wrong(self, client, create_user):
        token = "gabagoo"
        resp = client.post(
            f"/auth/reset_password/{token}", data={"password": "monkey", "password2": "monkey"})
        assert resp.status_code == 302
        assert "/index" in resp.headers.get("Location")

