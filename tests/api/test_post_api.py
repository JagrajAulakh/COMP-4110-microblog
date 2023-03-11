import pytest

from app import create_app, db
from app.models import User, Post
from app.api.auth import token_auth
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    ELASTICSEARCH_URL = None


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
        self.app_text_request_context.pop()

    @pytest.fixture()
    def user1(self):
        user = User(username="Joe", email="joe@joe.com")
        db.session.add(user)
        db.session.commit()
        yield user

    @pytest.fixture()
    def user2(self):
        user = User(username="Mama", email="mama@mama.com")
        db.session.add(user)
        db.session.commit()
        yield user

    @pytest.fixture()
    def post1(self, user1):
        post = Post(
            body="I think im the best one on this site frfr on G", user_id=user1.id
        )
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
        assert d["items"][0]["id"] == post1.id

    def test_get_post_invalid_user(self, headers):
        response = self.client.get("/api/posts/21380", headers=headers)
        assert response.status_code == 400

    def test_get_post_valid_user(self, user1, headers):
        response = self.client.get(
            "/api/posts/%d" % user1.id,
            headers=headers,
        )
        assert response.status_code == 200

    def test_post_post_invalid_user(self, headers):
        old_len = len(Post.query.all())

        response = self.client.post(
            "/api/posts/1000",
            json={"body": "This is a test post by user 1"},
            headers=headers,
        )

        assert response.status_code == 400
        assert len(Post.query.all()) == old_len

    def test_post_post_valid_user(self, user1, headers):
        old_len = len(Post.query.all())

        response = self.client.post(
            "/api/posts/%d" % user1.id,
            json={"body": "This is a test post by user 1"},
            headers=headers,
        )

        assert response.status_code == 201
        assert len(Post.query.all()) == old_len + 1

    def test_post_post_no_body(self, user1, headers):
        old_len = len(Post.query.all())
        response = self.client.post(
            "/api/posts/%d" % user1.id,
            headers=headers,
        )

        assert response.status_code == 400
        assert len(Post.query.all()) == old_len

    def test_post_post_wrong_user(self, user1, user2, headers):
        assert user1.id != user2.id

        response = self.client.post(
            "/api/posts/%d" % user2.id,
            json={
                "body": "I'm posting as another user that I am not authorized to post as"
            },
            headers=headers,
        )

        assert response.status_code == 400
        assert "permission" in response.data.decode("utf-8").lower()

    def test_delete_post_invalid_user(self, post1, headers):
        old_len = len(Post.query.all())

        response = self.client.delete(
            "api/posts/100", json={"id": post1.id}, headers=headers
        )

        assert response.status_code == 400
        assert len(Post.query.all()) == old_len

    def test_delete_post_valid_user(self, user1, post1, headers):
        old_len = len(Post.query.all())

        response = self.client.delete(
            "api/posts/%d" % user1.id, json={"id": post1.id}, headers=headers
        )

        assert response.status_code == 200
        assert len(Post.query.all()) == old_len - 1
        assert response.get_json()["id"] == post1.id

    def test_delete_post_no_id(self, user1, post1, headers):
        old_len = len(Post.query.all())

        response = self.client.delete("api/posts/%d" % user1.id, headers=headers)

        assert response.status_code == 400
        assert len(Post.query.all()) == old_len

    def test_delete_post_wrong_user(self, user1, user2, post1, headers):
        assert user1.id != user2.id

        response = self.client.delete(
            "/api/posts/%d" % user2.id,
            json={"id": post1.id},
            headers=headers,
        )

        assert response.status_code == 400

    def test_delete_post_invalid_post_id(self, user1, headers):
        response = self.client.delete(
            "/api/posts/%d" % user1.id,
            json={"id": 1000},
            headers=headers,
        )

        assert response.status_code == 404

    def test_like_post_no_post_id_in_body(self, user1, headers):
        response = self.client.post(
                "/api/post/like/%d" % user1.id,
                headers=headers
                )
        assert response.status_code == 400

    def test_like_post_valid_user(self, user1, post1, headers):
        old_likes = post1.likes.count()

        response = self.client.post(
                "/api/post/like/%d" % user1.id,
                json = {'post_id': post1.id},
                headers=headers
                )

        assert response.status_code == 200
        assert post1.likes.count() == old_likes + 1

    # User should only be able to like a post once
    def test_like_post_twice(self, user1, post1, headers):
        old_likes = post1.likes.count()

        response1 = self.client.post(
                "/api/post/like/%d" % user1.id,
                json = {'post_id': post1.id},
                headers=headers
                )
        assert response1.status_code == 200

        response2 = self.client.post(
                "/api/post/like/%d" % user1.id,
                json = {'post_id': post1.id},
                headers=headers
                )
        assert response2.status_code == 200
        assert post1.likes.count() == old_likes + 1

    def test_like_post_invalid_user(self, post1, headers):
        response = self.client.post(
                "/api/post/like/12345",
                json = {'post_id': post1.id},
                headers=headers
                )

        assert response.status_code == 400

    def test_like_post_wrong_user_token(self, user2, post1, headers):
        response = self.client.post(
                "/api/post/like/%d" % user2.id,
                json = {'post_id': post1.id},
                headers=headers
                )

        assert response.status_code == 400

    def test_unlike_post_no_post_id_in_body(self, user1, headers):
        response = self.client.post(
                "/api/post/unlike/%d" % user1.id,
                headers=headers
                )
        assert response.status_code == 400

    def test_unlike_post_valid_user(self, user1, post1, headers):
        user1.like(post1)
        old_likes = post1.likes.count()
        response = self.client.post(
                "/api/post/unlike/%d" % user1.id,
                json = {'post_id': post1.id},
                headers=headers
                )

        assert response.status_code == 200
        assert post1.likes.count() == old_likes - 1

    def test_unlike_post_twice(self, user1, post1, headers):
        user1.like(post1)
        old_likes = post1.likes.count()

        response1 = self.client.post(
                "/api/post/unlike/%d" % user1.id,
                json = {'post_id': post1.id},
                headers=headers
                )
        assert response1.status_code == 200

        response2 = self.client.post(
                "/api/post/unlike/%d" % user1.id,
                json = {'post_id': post1.id},
                headers=headers
                )
        assert response2.status_code == 200
        assert post1.likes.count() == old_likes - 1


    def test_unlike_post_invalid_user(self, post1, headers):
        response = self.client.post(
                "/api/post/unlike/12345",
                json = {'post_id': post1.id},
                headers=headers
                )

        assert response.status_code == 400

    def test_unlike_post_wrong_user_token(self, user2, post1, headers):
        response = self.client.post(
                "/api/post/unlike/%d" % user2.id,
                json = {'post_id': post1.id},
                headers=headers
                )

        assert response.status_code == 400

    def test_post_like_toggle(self, user1, post1, headers):
        old_likes = post1.likes.count()

        response = self.client.post(
                "api/post/toggle-like/%d" % user1.id,
                json = {'post_id': post1.id},
                headers=headers
                )
        assert response.status_code == 200
        assert post1.likes.count() == old_likes + 1

        response = self.client.post(
                "api/post/toggle-like/%d" % user1.id,
                json = {'post_id': post1.id},
                headers=headers
                )

        assert post1.likes.count() == old_likes
