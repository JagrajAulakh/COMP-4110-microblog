import pytest
from config import Config
from app import create_app, db
from app.models import User




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
        self.app_context.push()
        db.create_all()
        yield self.app.test_client()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()



    @pytest.fixture()
    def create_user(self):
        u1 = User(username='john', email='john@example.com')
        u1.set_password("batata")
        db.session.add(u1)
        db.session.commit()
        return u1


#checking if we are sent to login page
    def test_login(self, client, create_user):
        resp = client.get('/auth/login')
        assert resp.status_code is 200
        assert b'Sign In' in resp.data
        assert b'Register' in resp.data
        resp = client.post("/auth/login", data={
        "username": create_user.username,
        "password": "lala",})
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers.get("Location")
        print(resp.headers.get("Location"))
        resp = client.post("/auth/login", data={
        "username": create_user.username,
        "password": "batata",})
        assert resp.status_code == 302
        assert "index" in resp.headers.get("Location")



    def test_login_twice(self, client, create_user):
        resp = client.post("/auth/login", data={
        "username": create_user.username,
        "password": "batata",})
        resp = client.post("/auth/login", data={
        "username": create_user.username,
        "password": "lala",})
        assert "index" in resp.headers.get("Location")






    def test_login_invalid_username(self, client):
        resp = client.post("/auth/login", data={
        "username": "jagraj3",
        "password": "batata",})
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers.get("Location")






