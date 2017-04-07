# -*- coding: utf-8 -*-
from StringIO import StringIO
import socket

from flask.views import View
from flask import render_template, request, session, redirect, url_for, flash
from forms import NetworkForm, SSLForm, SPForm, ServiceForm, IDPForm, LDAPForm
from Crypto.PublicKey import RSA
from paramiko import SSHClient, AutoAddPolicy, RSAKey

def generate_rsa_key(bits=2048):
    key = RSA.generate(bits, e=65537)
    pub_key = key.publickey().exportKey("OpenSSH")
    priv_key = key.exportKey("OpenSSH")
    return priv_key, pub_key

class CustomView(View):
    methods = ["GET", "POST"]

    def __init__(self, template_name):
        self.template_name = template_name

    def get_template_name(self):
        return self.template_name

    def render_template(self, context):
        return render_template(self.get_template_name(), **context)

    def lock_session(self):
        session['locked'] = True

    def unlock_session(self):
        session['locked'] = False

    def is_locked(self):
        return session['locked'] == True

    def __verifyhosts(self):
        data = session['data'].copy()
        for k, v in session['data'].iteritems():
            if not v:
                data.pop(k)
        current_ip = socket.gethostbyname(socket.gethostname())

        diff = {}
        for k, v in data.iteritems():
            for _k, _v in data.get(k, {}).iteritems():
                if _k == "ip" and _v != current_ip:
                    diff[k] = _v
        if diff:
            session['ssh_ips'] = diff
            return redirect(url_for("sshview"))
        else:
            session['ssh_ips'] = diff
        return redirect(url_for("processview"))

    def next_view(self):
        try:
            session['next_view']
        except:
            return redirect(url_for("serviceview"))
        if len(session['next_view']) == 0:
            return self.__verifyhosts()
        url = session["next_view"].popitem()[1]
        if url:
            self.unlock_session()
            return redirect(url_for(url))
        return "No views." # TODO: BUG?

class ServiceView(CustomView):

    def dispatch_request(self):
        self.lock_session()
        form = ServiceForm(request.form)

        if request.method == "GET":
            context = {"form": form}
            return self.render_template(context)
        if request.method == "POST" and form.validate():
            views = {"sp": "spview", "idp": "idpview", "ldap": "ldapview"}
            for k, v in form.data.iteritems():
                if not v:
                    views[k] = False

            session['data'] = {k: None for k in views.keys()}
            session['next_view'] =  {k: v for (k, v) in views.iteritems() if v}
            return self.next_view()
        else:
            flash("Selecione pelo menos uma opção.")
            return redirect(url_for("serviceview")) # TODO: should we call render_template again?

class IDPView(CustomView):

    def dispatch_request(self):
        if self.is_locked():
            flash("Não autorizado.")
            return redirect(url_for("serviceview"))

        form = IDPForm(request.form)
        if request.method == "GET":
            context = {"form": form}
            return self.render_template(context)
        if request.method == "POST" and form.validate():
            tmp = session['data']
            tmp['idp'] = form.data
            session['data'] = tmp
            return self.next_view()
        return self.render_template({"form": form})

class SPView(CustomView):

    def dispatch_request(self):
        if self.is_locked():
            flash("Não autorizado.")
            return redirect(url_for("serviceview"))

        form = SPForm(request.form)
        if request.method == "GET":
            context = {"form": form}
            return self.render_template(context)
        if request.method == "POST" and form.validate():
            session['data']['sp'] = form.data
            return self.next_view()

class LDAPView(CustomView):

    def dispatch_request(self):
        if self.is_locked():
            flash("Não autorizado.")
            return redirect(url_for("serviceview"))

        form = LDAPForm(request.form)
        if request.method == "GET":
            context = {"form": form}
            return self.render_template(context)
        if request.method == "POST" and form.validate():
            tmp = session['data']
            tmp['ldap'] = form.data
            session['data'] = tmp
            return self.next_view()
        return self.render_template({"form": form})

class ProcessView(CustomView):
    pass

class SSHView(CustomView):

    def test_ssh(self, ip, priv_key, port=22):
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        try:
            client.connect(ip, port=port, username="root", pkey=\
                    RSAKey.from_private_key(StringIO(priv_key)))
            return True
        except:
            return False

    def dispatch_request(self):
        if self.is_locked():
            flash("Não autorizado.")
            return redirect(url_for("serviceview"))
        if request.method == "GET":
            if session['ssh']:
                priv_key = session['ssh'].get("priv")
                pub_key = session['ssh'].get("pub")
            else:
                priv_key, pub_key = generate_rsa_key()
                session['ssh'] = {"pub": pub_key, "priv": priv_key}
            return self.render_template({"key": pub_key, "ips": session['ssh_ips']})

        if request.method == "POST":
            ips = {"ldap": None, "sp": None, "idp": None}
            for k, v in session['data'].iteritems():
                if k in ips.keys() and session['data'].get(k, None):
                    ips[k] = session['data'].get(k).get("ip", None)
            tmp = ips.copy()
            for k, v in tmp.iteritems(): # TODO: refactor
                if v:
                    if self.test_ssh(v, \
                            session['ssh'].get("priv", "")):
                        ips.pop(k)
            if len(ips) == 0 and not all(ips.values()):
                return redirect(url_for("processview"))
            else:
                for k, v in ips.iteritems():
                    if v:
                        flash("Erro ao acessar o %s no IP %s" % (k, v))
                return self.render_template({"key": session['ssh'].get("pub"),
                    "ips": session['ssh_ips']})

