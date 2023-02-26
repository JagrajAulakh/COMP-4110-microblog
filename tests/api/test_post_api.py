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
    def user(self):
        user = User(username="Joe", email="joe@joe.com")
        db.session.add(user)
        db.session.commit()
        yield user

    @pytest.fixture()
    def headers(self, user):
        headers = {"Authorization": "Bearer {}".format(user.get_token())}
        return headers

    def test_get_posts(self, user, headers):
        response = self.client.get("/api/posts", headers=headers)
        assert response.data
        assert response.status_code == 200

        d = json.loads(response.data.decode())
        assert len(d["items"]) == 0

        post = Post(body="I think im the best one on this site frfr on G",
                    user_id=user.id)
        db.session.add(post)
        db.session.commit()
        assert Post.query.first() == post

        response = self.client.get("/api/posts", headers=headers)
        assert response.status_code == 200
        assert response.data
        d = json.loads(response.data.decode())
        assert len(d["items"]) == 1

