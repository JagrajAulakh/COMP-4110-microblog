# Microblog

This project is a web application built using Flask in Python that allows users to
create and share their blog posts and interact with other users.

## Key features

- User registration and login: Users are able to create an account and log in
- Profile management: Users are able to view and edit their profiles (name, profile picture, and bio)
- Posting: Users are able to create posts
- Viewing: Users are able to view reviews posted by other users
- Commenting: Users are able to add comments to posts by other users
- Follow/Unfollow: Users are able to follow/unfollow other users and see their reviews on a personalized timeline.
- Like/Dislike: Users are able to like and dislike reviews
- Bookmark: Users are able to bookmark reviews and products, so they can easily find them later.

## Installing and running

### Using Python

Make sure you have python 3 installed, preferably 3.10+ with `python -v`

- Clone the repo `git clone https://github.com/JagrajAulakh/COMP-4110-microblog.git`
- Setup virtual environment `python -m venv venv`
- Enter venv `source ./venv/bin/activate`
- Install dependencies:
	- `pip install -r ./requirements.txt`
	- `pip install gunicorn`
 - Run the application `./boot.sh`

The application will be running on [localhost:5000](http://localhost:5000)

### Using Docker

Make sure Docker and docker-compose are installed:

```bash
$ docker -v
Docker version 24.0.2, build cb74dfcd85

$ docker-compose -v
Docker Compose version 2.20.2
```

Run the application: `docker-compose up -d --build`

The application will be running on [localhost:5000](http://localhost:5000)
