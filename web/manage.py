# -*- coding: utf-8 -*
import os
from flask_script import Manager
from robot.views import app

manager = Manager(app)

if __name__ == "__main__":
    manager.run()
