import pytest
from app import create_app, db
from app.models import User
from config import Config

api_users_num = "/api/users/%d"
api_users = "/api/users"

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    ELASTICSEARCH_URL = None

class TestUserModel:
    @pytest.fixture(autouse=True)
    def setup_app(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_text_request_context = self.app.test_request_context()
        self.app_context.push()
        self.app_text_request_context.push()
        db.create_all()
        self.client = self.app.test_client()
        yield
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        self.app_text_request_context.pop()

    @pytest.fixture()
    def user1(self):
        u = User(username="joe", email="joe@joe.com")
        db.session.add(u)
        db.session.commit()
        yield u

    @pytest.fixture()
    def user2(self):
        user = User(username="Mama", email="mama@mama.com")
        db.session.add(user)
        db.session.commit()
        yield user

    @pytest.fixture()
    def headers(self, user1):
        headers = {"Authorization": "Bearer {}".format(user1.get_token())}
        return headers

    def test_get_user(self, user1, headers):
        response = self.client.get(
                api_users_num % user1.id,
                headers=headers
                )

        assert response.status_code == 200
        assert response.get_json()['id'] == user1.id

    def test_get_user_followers(self, user1, user2, headers):

        user2.follow(user1)

        response = self.client.get(
                "/api/users/%d/followers" % user1.id,
                headers=headers
                )

        assert response.status_code == 200
        assert response.get_json()['items'][0]['id'] == user2.id


    def test_get_user_followed(self, user1, user2, headers):
        user2.follow(user1)

        response = self.client.get(
                "/api/users/%d/followed" % user2.id,
                headers=headers
                )

        assert response.status_code == 200
        assert response.get_json()['items'][0]['id'] == user1.id


    def test_create_user_valid(self):
        response = self.client.post(api_users, json={
            'username': 'joemama420',
            'email': 'urmom@joemama.com',
            'password': 'mamajoe'
            })

        assert response.status_code == 201
        print(response.get_json())
        assert User.query.get(response.get_json()['id'])

    def test_create_user_no_email(self):
        response = self.client.post(api_users, json={
            'username': 'joemama420',
            'password': 'mamajoe'
            })

        assert response.status_code == 400

    def test_create_user_username_already_exists(self, user1):
        response = self.client.post(api_users, json={
            'username': user1.username,
            'email': 'urmom@joemama.com',
            'password': 'mamajoe'
            })

        assert response.status_code == 400

    def test_create_user_email_already_exists(self, user1):
        response = self.client.post(api_users, json={
            'username': 'joemama420',
            'email': user1.email,
            'password': 'mamajoe'
            })

        assert response.status_code == 400

    def test_update_user_username(self, user1, headers):
        response = self.client.put(api_users_num % user1.id, json={
            'username': 'legend27',
            }, headers=headers)

        assert response.status_code == 200
        assert response.get_json()['id'] == user1.id
        assert response.get_json()['username'] == 'legend27'


    def test_update_user_invalid_user_token(self, user2, headers):
        response = self.client.put(api_users_num % user2.id, json={
            'username': 'legend27',
            }, headers=headers)

        assert response.status_code == 403
