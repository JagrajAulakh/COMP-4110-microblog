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


class TestUserModel:
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

    def test_password_hashing(self):
        u = User(username="susan")
        u.set_password("cat")
        assert not u.check_password("dog")
        assert u.check_password("cat")

    def test_avatar(self):
        u = User(username="john", email="john@example.com")
        assert u.avatar(128) == (
            "https://www.gravatar.com/avatar/d4c74594d841139328695756648b6bd6?d=identicon&s=128"
        )

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        assert u1.followed.all() == []
        assert u1.followers.all() == []

        u1.follow(u2)
        db.session.commit()
        assert u1.is_following(u2) is True
        assert u1.followed.count() == 1
        assert u1.followed.first().username == 'susan'
        assert u2.followers.count() == 1
        assert u2.followers.first().username == 'john'

        u1.unfollow(u2)
        db.session.commit()
        assert not u1.is_following(u2)
        assert u1.followed.count() == 0
        assert u2.followers.count() == 0

    def test_follow_posts(self):
        # create four users
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        # create four posts
        now = datetime.utcnow()
        p1 = Post(body="post from john", author=u1,
                  timestamp=now + timedelta(seconds=1))
        p2 = Post(body="post from susan", author=u2,
                  timestamp=now + timedelta(seconds=4))
        p3 = Post(body="post from mary", author=u3,
                  timestamp=now + timedelta(seconds=3))
        p4 = Post(body="post from david", author=u4,
                  timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        # setup the followers
        u1.follow(u2)  # john follows susan
        u1.follow(u4)  # john follows david
        u2.follow(u3)  # susan follows mary
        u3.follow(u4)  # mary follows david
        db.session.commit()

        # check the followed posts of each user
        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        assert f1 == [p2, p4, p1]
        assert f2 == [p2, p3]
        assert f3 == [p3, p4]
        assert f4 == [p4]

    def test_get_reset_password_token_valid_secret(self, new_user):
        password = "password"
        new_user.set_password(password)

        reset_token = new_user.get_reset_password_token()

        assert reset_token
        data = jwt.decode(reset_token, TestConfig.SECRET_KEY, algorithms=["HS256"])
        assert data.get('reset_password', None) == new_user.id

    def test_get_reset_password_token_invalid_secret(self, new_user):
        reset_token = new_user.get_reset_password_token()
        try:
            _ = jwt.decode(reset_token, 'not_so_secret_key...also_invalid', algorithms=["HS256"])
            assert False
        except jwt.InvalidSignatureError:
            assert True

    def test_verify_reset_password_token_valid_secret(self, new_user):
        encoded_token = jwt.encode(
                {'reset_password': new_user.id}, TestConfig.SECRET_KEY, algorithm="HS256")
        
        user = new_user.verify_reset_password_token(encoded_token)
        assert user.id == new_user.id

    def test_verify_reset_password_token_invalid_secret(self, new_user):
        encoded_token = jwt.encode(
                {'reset_password': new_user.id}, 'not_so_secret_key...also_invalid', algorithm="HS256")
        user = new_user.verify_reset_password_token(encoded_token)
        assert user is None

    def test_user_from_dict_with_password(self, new_user):
        user_dict = {
                'username': 'joe',
                'email': 'joe@joe.com',
                'about_me': 'Hi, I\'m Joe... Joe MAMA!',
                'password': 'super_secret_password'
                }

        new_user.from_dict(user_dict, new_user=True)

        assert new_user.username == user_dict['username']
        assert new_user.email == user_dict['email']
        assert new_user.check_password(user_dict['password'])


    def test_user_from_dict_no_password(self, new_user):
        user_dict = {
                'username': 'joe',
                'email': 'joe@joe.com',
                'about_me': 'Hi, I\'m Joe... Joe MAMA!',
                }

        new_user.from_dict(user_dict)

        assert new_user.username == user_dict['username']
        assert new_user.email == user_dict['email']
        assert new_user.password_hash is None

    def test_user_to_dict(self, new_user):
        data = new_user.to_dict(include_email=True)

        assert type(data) == dict

        assert data['id'] == new_user.id
        assert data['username'] == new_user.username
        assert data['email'] == new_user.email
        assert data['about_me'] == new_user.about_me

    def test_user_get_token(self, new_user: User):
        assert new_user.token is None
        token = new_user.get_token()
        assert token is not None
        new_token = new_user.get_token()
        assert new_token == token
        assert datetime.utcnow() < new_user.token_expiration

    def test_user_revoke_token(self, mocker, new_user: User):
        TOKEN = 'thisisthetoken'
        mocker.patch('app.models.User.get_token', return_value=TOKEN)
        token = new_user.get_token()
        assert token == TOKEN

        new_user.revoke_token()
        assert datetime.utcnow() > new_user.token_expiration

    def test_user_check_token_valid(self, new_user):
        token = new_user.get_token()
        assert User.check_token(token).id == new_user.id

    def test_user_check_token_invalid(self, new_user):
        _ = new_user.get_token()
        assert User.check_token('garbage') is None

    def test_user_check_token_expired(self, mocker, new_user):
        TOKEN = 'thisisthetoken'
        mocker.patch.object(User, 'token', TOKEN)
        mocker.patch('app.models.User.get_token', return_value=TOKEN)
        new_user.token_expiration = datetime.utcnow()-timedelta(seconds=1)

        assert User.check_token(new_user.get_token()) is None

    @pytest.fixture()
    def new_post(self, new_user):
        p = Post(
                user_id = new_user.id,
                body=f"This is a new post by user {new_user.username}"
                )
        yield p

    def test_user_like_post(self, new_user, new_post):
        user_liked = new_user.liked.count()
        post_likes = new_post.likes.count()

        new_user.like(new_post)

        assert new_user.liked.count() == user_liked+1
        assert new_post.likes.count() == post_likes+1

    def test_user_unlike(self, new_user, new_post):
        new_user.like(new_post)

        user_liked = new_user.liked.count()
        post_likes = new_post.likes.count()

        new_user.unlike(new_post)

        assert new_user.liked.count() == user_liked-1
        assert new_post.likes.count() == post_likes-1
