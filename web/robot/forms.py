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
from wtforms import PasswordField
from wtforms.fields.html5 import EmailField

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
    gateway = StringField(u"Gateway", validators=[validators.Required()]) # TODO
    dns = StringField(u"DNS", validators=[validators.Required()]) # TODO
    mask = StringField(u"Mascara", validators=[validators.Required()])

br_states = [ # this is temporary
        ('AC', u'Acre'),
        ('AL', u'Alagoas'),
        ('AP', u'Amapá'),
        ('AM', u'Amazonas'),
        ('BA', u'Bahia'),
        ('CE', u'Ceará'),
        ('DF', u'Distrito Federal'),
        ('ES', u'Espírito Santo'),
        ('GO', u'Goiás'),
        ('MA', u'Maranhão'),
        ('MT', u'Mato Grosso'),
        ('MS', u'Mato Grosso do Sul'),
        ('MG', u'Minas Gerais'),
        ('PA', u'Pará'),
        ('PB', u'Paraíba'),
        ('PR', u'Paraná'),
        ('PE', u'Pernambuco'),
        ('PI', u'Piauí'),
        ('RJ', u'Rio de Janeiro'),
        ('RN', u'Rio Grande do Norte'),
        ('RS', u'Rio Grande do Sul'),
        ('RO', u'Rondônia'),
        ('RR', u'Roraima'),
        ('SC', u'Santa Catarina'),
        ('SP', u'São Paulo'),
        ('SE', u'Sergipe'),
        ('TO', u'Tocantins')]

class TechnicalDetails(Form):
    technical_name = StringField(u"Nome do técnico", validators=[validators.Required()])
    technical_email = EmailField(u"Email do técnico", validators=[validators.Required(),
        validators.Email()])

class CountryForm(Form):
    city = StringField(u"Cidade", validators=[validators.Required()])
    state = SelectField(u"Estado", choices=br_states, validators=[
        validators.Required()])
    organization_name = StringField(u"Nome da organização", validators=[
        validators.Required()])
    country = SelectField(u"País", choices=[("BR", "Brasil")], validators=[validators.Required()])
    organization_initials = StringField(u"Iniciais da organização",
            validators=[validators.Required()])

class IDPForm(NetworkForm, CountryForm, TechnicalDetails):
    port = SelectMultipleField(u"Porta", validators=[validators.Required()],
            choices=[(443, 443), (80, 80)], coerce=int)
    institution_name = StringField(u"Nome da instituição", validators=[
        validators.Required()])
    keystore_pwd = PasswordField(u"Senha para o keystore", validators=[
        validators.DataRequired(), validators.EqualTo("confirm", message=u"As senhas devem coincidir.")])
    confirm = PasswordField(u"Confirme sua senha.")
    # technical_email = EmailField(u"Email do técnico", validators=[validators.Required(),
    #     validators.Email()])
    # technical_name = StringField(u"Nome do técnico", validators=[validators.Required()])
    install_path = StringField(u"Caminho da instalação", validators=[validators.Required()])

class SPForm(Form):
    pass

class LDAPForm(NetworkForm, CountryForm):
    url = StringField(u"URL LDAP", validators=[validators.Required(),
        validators.URL()])
    query_dn = StringField(u"DN de consulta", validators=[validators.Required()])
    read_dn = StringField(u"DN de leitura", validators=[validators.Required()])
    port = IntegerField(u"Porta", default=389, validators=[validators.Required()])
    researcher_password = PasswordField(u"Senha para o keystore", validators=[
        validators.DataRequired(), validators.EqualTo("confirm",
            message=u"As senhas devem coincidir.")])
    confirm = PasswordField(u"Confirme sua senha.")
    starttls = BooleanField(u"Usar StartTLS", validators=[validators.Required()])
    ldap_password = PasswordField(u"Senha para o keystore", validators=[
        validators.DataRequired(), validators.EqualTo("confirm_ldap",
            message=u"As senhas devem coincidir.")])
    confirm_ldap = PasswordField(u"Confirme sua senha.")

class SSLForm(CountryForm):
    email = EmailField(u"Email", validators=[validators.Required(),
        validators.Email()])
    # TODO
