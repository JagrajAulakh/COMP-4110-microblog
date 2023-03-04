import jwt
import pytest
from pytest_mock import mocker
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Post
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    ELASTICSEARCH_URL = None


class TestPostModel:
    @pytest.fixture(autouse=True)
    def setup_app(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_text_request_context = self.app.test_request_context()
        self.app_context.push()
        self.app_text_request_context.push()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @pytest.fixture()
    def new_user(self):
        u = User(username="joe", email="joe@joe.com")
        db.session.add(u)
        db.session.commit()
        yield u

    @pytest.fixture()
    def new_post(self, new_user):
        p = Post(user_id=new_user.id, body="This is the body of my post!")
        db.session.add(p)
        db.session.commit()
        yield p

    
    def test_post_from_dict(self, new_user):
        p = Post()
        data = {
                "user_id": new_user.id,
                "body": "Walter White is goated"
                }
        assert p.body is None
        assert p.user_id is None

        p.from_dict(data)

        assert "walter white" in p.body.lower()
        assert p.user_id == new_user.id


    def test_post_to_dict(self, new_user, new_post):
        data = new_post.to_dict()

        assert data['body'] == new_post.body
        assert data['user_id'] == new_user.id
        print(data)
