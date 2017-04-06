import socket
import os

from wtforms import Form
from wtforms import ValidationError
from wtforms import StringField
from wtforms import SelectField, SelectMultipleField
from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import validators

class ServiceForm(Form):
    ldap = BooleanField("LDAP")
    sp = BooleanField("SP")
    idp = BooleanField("IDP")

class NetworkForm(Form):
    ip = StringField("Endereco IP", default=socket.gethostbyname(
        socket.gethostname()), validators=[validators.IPAddress(),
            validators.Required()])
    domain = StringField("Dominio", default=socket.getfqdn(),
            validators=[validators.Required()]) # TODO, split
    hostname = StringField("Hostname", default=socket.gethostname(),
            validators=[validators.Required()])
    # gateway = ..
    # dns = ...
    # mas = ..

class IDPForm(NetworkForm):
    port = SelectMultipleField("Porta", validators=[validators.Required()],
            choices=[(443, 443), (80, 80)])
    institution_name = StringField(validators.required())

class SPForm(Form):
    pass

class LDAPForm(NetworkForm):
    url = StringField("URL LDAP", validators=[validators.Required(),
        validators.URL()])
    query_dn = StringField("DN de consulta", validators=[validators.Required()])
    read_dn = StringField("DN de leitura", validators=[validators.Required()])
    port = IntegerField("Porta", default=389, validators=[validators.Required()])

class SSLForm(Form):
    pass
