import os

from flask import Flask
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View

from views.views import ServiceView
from views.views import IDPView
from views.views import SPView
from views.views import LDAPView
from views.views import ProcessView

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
Bootstrap(app)
nav = Nav()

@nav.navigation()
def global_nav():
    return Navbar("Gidlab", View("Configuracao de servico", "serviceview"))

nav.init_app(app)

app.add_url_rule('/', view_func=ServiceView.as_view('serviceview', template_name="service.html"))
app.add_url_rule('/idp', view_func=IDPView.as_view("idpview", template_name="idp.html"))
app.add_url_rule('/sp', view_func=SPView.as_view("spview", template_name="sp.html"))
app.add_url_rule('/ldap', view_func=SPView.as_view("ldapview", template_name="ldap.html"))
app.add_url_rule('/process', view_func=ProcessView.as_view("processview", template_name="process.html"))

manager = Manager(app)

if __name__ == "__main__":
    manager.run()
