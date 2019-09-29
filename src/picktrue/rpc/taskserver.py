from threading import Thread

from flask import Flask, jsonify
from flask import request

from picktrue.rpc.channel import BrowserRequester

app = Flask(__name__)


__all__ = [
    "server",
]


class TaskServer:
    def __init__(self):
        self.requester = BrowserRequester()
        self._thread = None

    def request(self, url):
        return self.requester.send_and_wait(url)

    def log_received(self):
        while True:
            resp = self.request("https://www.artstation.com/users/braveking/projects.json?page=1")
            print("resp received", resp)

    def start_debug_task(self):
        t = Thread(target=self.log_received)
        t.setDaemon(True)
        t.start()

    def is_running(self):
        if self._thread is None:
            return False
        if not self._thread.is_alive():
            return False
        return True

    def start(self):
        if self.is_running():
            return False

        def run():
            app.run(debug=True, port=2333, use_reloader=False)

        self._thread = Thread(target=run)
        self._thread.setDaemon(True)
        self._thread.start()


server = TaskServer()


@app.route("/tasks/")
def get_task():
    task = server.requester.get_request(10)
    if task is None:
        return jsonify([])
    else:
        return jsonify([task, ])


@app.route("/tasks/submit/", methods=["POST", "GET"])
def task_submit():
    """
    :return:
    """
    resp = request.get_json(force=True)
    server.requester.submit_response(
        resp
    )
    return jsonify({})


if __name__ == '__main__':
    server.start()
    # server.start_debug_task()
    import pdb;pdb.set_trace()
