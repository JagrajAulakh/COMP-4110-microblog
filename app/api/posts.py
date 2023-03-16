from flask import jsonify, request, url_for
from flask_login import current_user
from app import db
from app.api.errors import bad_request, error_response
from app.models import Post, User, Favorite
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


@bp.route("/posts/<int:id>", methods=["GET", "POST", "DELETE", "FAVORITE", "UNFAVORITE", "UNFAVORITE_DELETED_POST"])
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

    # Deletes the post
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
    
    # Adds post to the user's favorites list
    elif request.method == "FAVORITE":
        if "id" not in data:
            return bad_request("Must include id field")
        post = Post.query.get(int(data["id"]))
        if post is None:
            return error_response(404, "post with id %s not found (requested from user %d)" %
                               (data["id"], user.id))
        else:
            user.favorite(post)
            db.session.commit()
            return jsonify({"response":"Favorited post successfully."})
    
    # Removes post from the user's favorites list (does not work for deleted posts)
    elif request.method == "UNFAVORITE":
        if "id" not in data:
            return bad_request("Must include id field")
        post = Post.query.get(int(data["id"]))
        if post is None:
            return error_response(404, "post with id %s not found (requested from user %d)" %
                               (data["id"], user.id))
        else:
            user.unfavorite(post)
            db.session.commit()
            return jsonify({"response":"Unfavorited post successfully."})
    
    # Removes DELETED post from the user's favorites list        
    elif request.method == "UNFAVORITE_DELETED_POST":
        if "id" not in data:
            return bad_request("Must include id field")
        fave_post = user.favorites.filter_by(post_id=int(data["id"])).first()
        if fave_post is None:
            return error_response(404, "post with id %s not found (requested from user %d)" %
                               (data["id"], user.id))
        else:
            db.session.delete(fave_post)
            db.session.commit()
            return jsonify({"response":"Unfavorited post successfully."})
@bp.route('post/like/<int:id>', methods=["POST"])
def like_post(id):

    data = request.get_json() or {}
    if 'post_id' not in data:
        return bad_request("must include id field")

    user = User.query.get(id)
    if user is None:
        return bad_request("no user with id %s found" % id)
    if current_user.id != id:
        return bad_request("you do not have permission to post as user %s. You are logged in as user %s"
                           % (user.id, token_auth.current_user().id))


    post = Post.query.get(int(data["post_id"]))
    user.like(post)
    db.session.commit()

    response = jsonify(post.to_dict())
    response.status_code = 200

    return response

@bp.route('post/unlike/<int:id>', methods=["POST"])
def unlike_post(id):

    data = request.get_json() or {}
    if 'post_id' not in data:
        return bad_request("must include id field")

    user = User.query.get(id)
    if user is None:
        return bad_request("no user with id %s found" % id)
    if current_user.id != id:
        return bad_request("you do not have permission to post as user %s. You are logged in as user %s"
                           % (user.id, token_auth.current_user().id))


    post = Post.query.get(int(data["post_id"]))
    user.unlike(post)
    db.session.commit()

    response = jsonify(post.to_dict())
    response.status_code = 200

    return response


@bp.route('post/toggle-like/<int:id>', methods=["POST"])
def post_toggle_like(id):

    data = request.get_json() or {}
    if 'post_id' not in data:
        return bad_request("must include id field")

    user = User.query.get(id)
    if user is None:
        return bad_request("no user with id %s found" % id)
    if current_user.id != id:
        return bad_request("you do not have permission to post as user %s. You are logged in as user %s"
                           % (user.id, token_auth.current_user().id))

    post = Post.query.get(int(data["post_id"]))

    if user in post.likes:
        l = False
        user.unlike(post)
    else:
        l = True
        user.like(post)

    db.session.commit()

    response = jsonify({"result": "liked" if l else "unliked", "post": post.to_dict()})
    response.status_code = 200

    return response
