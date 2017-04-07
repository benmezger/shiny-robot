# -*- coding: utf-8 -*-
import socket
import os

from wtforms import Form
from wtforms import ValidationError
from wtforms import StringField
from wtforms import SelectField, SelectMultipleField
from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import validators

class ServiceForm(Form): # TODO: Fix validation, make sure at least one if required
    ldap = BooleanField("LDAP")
    sp = BooleanField("SP")
    idp = BooleanField("IDP")

class NetworkForm(Form):
    ip = StringField(u"Endereço IP", default=socket.gethostbyname(
        socket.gethostname()), validators=[validators.IPAddress(),
            validators.Required()])
    domain = StringField(u"Domínio", default=socket.getfqdn(),
            validators=[validators.Required()]) # TODO, split
    hostname = StringField(u"Hostname", default=socket.gethostname(),
            validators=[validators.Required()])
    # gateway = ..
    # dns = ...
    # mas = ..

class IDPForm(NetworkForm):
    port = SelectMultipleField("Porta", validators=[validators.Required()],
            choices=[(443, 443), (80, 80)], coerce=int)
    institution_name = StringField(u"Nome da instituição", validators=[
        validators.Required()])

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
