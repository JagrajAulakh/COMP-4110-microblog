from flask import jsonify, request, url_for
from app import db
from app.api.errors import bad_request, error_response
from app.models import Post, User
from app.api import bp
from app.api.auth import token_auth


# Get all posts by all users
@bp.route("/posts", methods=["GET"])
@token_auth.login_required
def get_posts():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Post.to_collection_dict(Post.query, page, per_page, "api.get_posts")
    return jsonify(data)


@bp.route("/posts/<int:id>", methods=["GET", "POST", "DELETE"])
@token_auth.login_required
def posts(id):
    user = User.query.get(id)
    if user is None:
        return bad_request("no user with id %s found" % id)
    data = request.get_json() or {}
    # Get all posts by a specific user
    if request.method == "GET":
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 10, type=int), 100)
        data = Post.to_collection_dict(Post.query, page, per_page, "api.posts", id=id)
        return jsonify(data)

    # Create a post by a specific user
    elif request.method == "POST":
        if "body" not in data:
            return bad_request("must include body field")
        if token_auth.current_user().id != user.id:
            print("token_user:", token_auth.current_user(), "\npassed user:", user)
            return bad_request("you do not have permission to post as user %s. You are logged in as user %s"
                               % (user.id, token_auth.current_user().id))

        post = Post()
        data['user_id'] = user.id
        post.from_dict(data)

        db.session.add(post)
        db.session.commit()
        response = jsonify(post.to_dict())
        response.status_code = 201
        response.headers['Location'] = url_for('main.index')

        return response

    elif request.method == "DELETE":
        if token_auth.current_user().id != user.id:
            return bad_request("you do not have permission to post as user %s. You are logged in as user %s"
                               % (user.id, token_auth.current_user().id))
        if "id" not in data:
            return bad_request("must include id field")

        post = user.posts.filter_by(id=int(data["id"])).first()
        if post is None:
            return error_response(404, "post with id %s not found from user %d" %
                               (data["id"], user.id))

        db.session.delete(post)
        db.session.commit()
        response = jsonify(post.to_dict())
        response.status_code = 200
        return response

