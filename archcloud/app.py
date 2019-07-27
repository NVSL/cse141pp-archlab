from flask import Flask
from flask import request
import logging as log
import run
import json

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route("/run-job", methods=['post'])
def run_job():
    sub = run.Submission._fromdict(json.loads(request.values['payload']))
    r = run.run_submission_locally(sub)
    return json.dumps(r._asdict())


if __name__ == '__main__':
    log.basicConfig(format="%(levelname)-8s [%(filename)s:%(lineno)d]  %(message)s", level=log.DEBUG)
    app.run(host="0.0.0.0")
