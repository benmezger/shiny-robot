# -*- coding: utf-8 -*
import os

from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View

from views import app
from views import ServiceView
from views import IDPView
from views import SPView
from views import LDAPView
from views import ProcessView

app.secret_key = os.environ.get("SECRET_KEY")
Bootstrap(app)
nav = Nav()

@nav.navigation()
def global_nav():
    return Navbar("Gidlab", View(u"Configuração de Serviços", "serviceview"))

nav.init_app(app)

app.add_url_rule('/', view_func=ServiceView.as_view('serviceview', template_name="service.html"))
app.add_url_rule('/idp', view_func=IDPView.as_view("idpview", template_name="idp.html"))
app.add_url_rule('/sp', view_func=SPView.as_view("spview", template_name="sp.html"))
app.add_url_rule('/ldap', view_func=LDAPView.as_view("ldapview", template_name="ldap.html"))
app.add_url_rule('/process', view_func=ProcessView.as_view("processview", template_name="process.html"))
# app.add_url_rule("/ssh", view_func=SSHView.as_view("sshview", template_name="ssh.html"))


