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



class TestMainRoutes:
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

    def test_

