# Performance tests

These tests are for stress testing the production server (or even your local if you
want) using the `locust` library.

## How to run

Make sure you have locust installed by running the following **in the project root**:

```sh
source venv/bin/activate # Activate the virtual environment
pip install -r requirements.txt # Install dependencies
```

Then run the locust tool (assuming you're testing your local dev server):

```sh
locust -H http://localhost:5000 -f TESTFILE.py
```

Then navigate to [localhost:8089](http://0.0.0.0:8089) to see the locust web interface.
Set your testing parameters, and click start
