import pytest
from config import Config
from app import create_app, db
from app.models import User
from flask_login import login_user, current_user
from pytest_mock import mocker
import flask_login

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
    def create_user(self):
        u1 = User(username="john", email="john@example.com")
        u1.set_password("batata")
        db.session.add(u1)
        db.session.commit()
        return u1

    def test_two_FA_hopt(self):
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
        resp = client.get("/auth/login")
        assert resp.status_code == 200
        assert b"Sign In" in resp.data
        assert b"Register" in resp.data

    def test_login_invalid_password(self, client, create_user):
        resp = client.post(
            "/auth/login",
            data={
                "username": create_user.username,
                "password": "lala",
            },
        )
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers.get("Location")

    def test_login_valid_user(self, client, create_user):
        resp = client.post(
            "/auth/login",
            data={
                "username": create_user.username,
                "password": "batata",
            },
        )
        assert resp.status_code == 302
        assert "index" in resp.headers.get("Location")

    def test_login_twice(self, client, create_user):
        resp = client.post(
            "/auth/login",
            data={
                "username": create_user.username,
                "password": "batata",
            },
        )
        resp = client.post(
            "/auth/login",
            data={
                "username": create_user.username,
                "password": "lala",
            },
        )
        assert "index" in resp.headers.get("Location")

    def test_login_invalid_username(self, client):
        resp = client.post(
            "/auth/login",
            data={
                "username": "jagraj3",
                "password": "batata",
            },
        )
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers.get("Location")


    def test_logout(self, client, create_user):
        resp = client.get("/auth/logout")
        assert resp.status_code == 302
        assert "index" in resp.headers.get("Location")


    def test_register_get(self, client):
    	resp = client.get("/auth/register")
    	assert resp.status_code == 200


    def test_register_create_user(self, client):
        resp = client.post(
            "/auth/register",
            data={
                "username": "wannabe",
                "email": "wannabe@gmail.com",
                "password": "batata",
                "password2": "batata",
            },
        )

    def test_register_redirect(self, mocker, client, create_user):
        resp = client.post(
            "/auth/login",
            data={
                "username": create_user.username,
                "password": "batata",
            },
        )
        resp = client.post(
            "/auth/register",
            data={
                "username": create_user.username,
                "email": create_user.email,
                "password": "batata",
                "password2": "batata",
            },)
        assert resp.status_code == 302
       	assert "/index" in resp.headers.get("Location")

    def test_reset_password(self, client, create_user):
        resp = client.post(
            "/auth/reset_password_request",
            data={
                "email": create_user.email
            },)
        assert resp.status_code == 302
