from white_party import app
from white_party.modules import Law, Users
import flask_whooshalchemy
from white_party.scheduled_tasks import TaskManager
from multiprocessing import Process

tasks = Process(target=TaskManager.run_tasks)

if __name__ == "__main__":
    tasks.start()
    flask_whooshalchemy.whoosh_index(app, Law)
    flask_whooshalchemy.whoosh_index(app, Users)
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
