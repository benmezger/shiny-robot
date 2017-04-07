# -*- coding: utf-8 -*-

from flask.views import View
from flask import render_template, request, session, redirect, url_for, flash
from forms import NetworkForm, SSLForm, SPForm, ServiceForm, IDPForm, LDAPForm
from Crypto.PublicKey import RSA

def generate_rsa_key(bits=2048):
    key = RSA.generate(bits, e=65537)
    pub_key = key.publickey().exportKey("PEM")
    priv_key = key.exportKey("PEM")
    return priv_key, pub_key

class CustomView(View):
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

    def next_view(self):
        if len(session['next_view']) == 0:
            return "TODO" # TODO: redirect to ProcessView
        url = session["next_view"].popitem()[1]
        if url:
            self.unlock_session()
            return redirect(url_for(url))
        return "No views." # TODO: BUG?

class ServiceView(CustomView):
    methods = ["GET", "POST"]

    def dispatch_request(self):
        self.lock_session()
        form = ServiceForm(request.form)

        if request.method == "GET":
            context = {"form": form}
            return self.render_template(context)
        if request.method == "POST" and form.validate():
            print "IS VALID"
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
    methods = ["GET", "POST"]

    def dispatch_request(self):
        if self.is_locked():
            flash("Não autorizado.")
            return redirect(url_for("serviceview"))

        form = IDPForm(request.form)
        if request.method == "GET":
            context = {"form": form}
            return self.render_template(context)
        if request.method == "POST" and form.validate():
            session['data']['idp'] = form.data
            return self.next_view()

class SPView(CustomView):
    methods = ["GET", "POST"]

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

def LDAPView(CustomView):
    methods = ["GET", "POST"]

    def dispatch_request(self):
        if self.is_locked():
            flash("Não autorizado.")
            return redirect(url_for("serviceview"))

        form = LDAPForm(request.form)
        if request.method == "GET":
            context = {"form", form}
            return self.render_template(context)
        if request.method == "POST" and form.validate():
            session['data']['ldap'] = form.data
            return self.next_view()

class ProcessView(CustomView):
    pass

