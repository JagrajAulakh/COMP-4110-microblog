from base64 import b64encode
import pytest
import json
from datetime import datetime, timedelta
from flask import testing

from werkzeug.datastructures import Headers
from app import create_app, db
from app.models import User, Post
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    ELASTICSEARCH_URL = None


# class TestClient(testing.FlaskClient):
#     def open(self, *args, **kwargs):
#         api_key_headers = Headers({"Authorization": "Bearer %s" % kwargs["token"]})
#         headers = kwargs.pop("headers", Headers())
#         headers.extend(api_key_headers)
#         kwargs["headers"] = headers
#         return super().open(*args, **kwargs)
#


class TestPostAPI:
    @pytest.fixture(autouse=True)
    def setup_app(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_text_request_context = self.app.test_request_context()
        self.app_context.push()
        self.app_text_request_context.push()
        db.create_all()
        # self.app.test_client_class = TestClient
        self.client = self.app.test_client()
        yield
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @pytest.fixture()
    def user1(self):
        user = User(username="Joe", email="joe@joe.com")
        db.session.add(user)
        db.session.commit()
        yield user

    @pytest.fixture()
    def post1(self, user1):
        post = Post(body="I think im the best one on this site frfr on G",
                    user_id=user1.id)
        db.session.add(post)
        db.session.commit()
        yield post

    @pytest.fixture()
    def headers(self, user1):
        headers = {"Authorization": "Bearer {}".format(user1.get_token())}
        return headers

    def test_get_posts_empty(self, headers):
        response = self.client.get("/api/posts", headers=headers)
        assert response.data
        assert response.status_code == 200

        d = response.get_json()
        assert len(d["items"]) == 0

    def test_get_posts_not_empty(self, post1, headers):
        assert Post.query.first() == post1

        response = self.client.get("/api/posts", headers=headers)
        assert response.status_code == 200
        assert response.data
        d = response.get_json()
        assert len(d["items"]) == 1

    def test_get_post_invalid_user(self, headers):
        response = self.client.get("/api/posts/21380", headers=headers)
        assert response.status_code == 400

    def test_get_post_valid_user(self, user1, headers):
        response = self.client.get("/api/posts/1", data={"id": user1.id, "page": 1, "per_page": 10}, headers=headers)
        assert response.status_code == 200

