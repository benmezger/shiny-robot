# -*- coding: utf-8 -*-
from StringIO import StringIO
import socket
import os
import subprocess
import time
import tempfile
import shutil

from flask.views import View
from flask import Flask
from flask import Response, stream_with_context
from flask import render_template, request, session, redirect, url_for, flash
from forms import NetworkForm, SSLForm, SPForm, ServiceForm, IDPForm, LDAPForm
from Crypto.PublicKey import RSA
from jinja2 import Environment, FileSystemLoader
import git

app = Flask(__name__)

# from paramiko import SSHClient, AutoAddPolicy, RSAKey

# def generate_rsa_key(bits=2048):
#    key = RSA.generate(bits, e=65537)
#    pub_key = key.publickey().exportKey("OpenSSH")
#    priv_key = key.exportKey("OpenSSH")
#    return priv_key, pub_key

def config_replacer(filepath, dir, **kwargs): # TODO, fix me
    # if not os.path.isfile(filepath) or not os.path.exists(filepath):
    #    return
    env = Environment(loader=FileSystemLoader(dir))
    template = env.get_template(filepath)
    out = template.render(**kwargs)
    return out

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

#     def __verifyhosts(self):
#         data = session['data'].copy()
#         for k, v in session['data'].iteritems():
#             if not v:
#                 data.pop(k)
#         current_ip = socket.gethostbyname(socket.gethostname())
#
#         diff = {}
#         for k, v in data.iteritems():
#             for _k, _v in data.get(k, {}).iteritems():
#                 if _k == "ip" and _v != current_ip:
#                     diff[k] = _v
#         if diff:
#             session['ssh_ips'] = diff
#             return redirect(url_for("sshview"))
#         else:
#             session['ssh_ips'] = diff
#         return redirect(url_for("processview"))

    def next_view(self):
        try:
            session['next_view']
        except:
            return redirect(url_for("serviceview"))
        if len(session['next_view']) == 0:
            return redirect(url_for("processview"))
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
        del form.organization_initials
        del form.state
        del form.organization_name
        del form.city

        if request.method == "GET":
            context = {"form": form}
            return self.render_template(context)
        if request.method == "POST" and form.validate():
            tmp = session['data']
            tmp['idp'] = form.data
            session['data'] = tmp
            if not session['next_view'].has_key('ldap'):
                session['next_view']['ldap'] = "ldapview"
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

    def inject_docker(self, path, filename="Dockerfile", **kwargs):
        out = config_replacer(filename, path, **kwargs)
        with open(os.path.join(path, filename, "w")) as f:
            f.write(out)

    def inject_idp(self, path, conf_dir="conf/", **kwargs):
        cpath = os.path.join(path, conf_dir)
        for _ in os.listdir(cpath):
            out = config_replacer(_, cpath, **kwargs)
            with open(os.path.join(cpath, _), "w") as f:
                f.write(out)

    def generate_config(self):
        data = session.get("data", {})
        if data:
            s = data['idp']['domain']
            data['idp']['scope'] = s.split(".")[1:] # ignore hostname
        conf_path = git.Repo(__file__, search_parent_directories=True)
        conf_path = conf_path.git.rev_parse("--show-toplevel")
        conf_path = os.path.join(conf_path, "docker-shibboleth")

        tmp_root_dir = tempfile.mkdtemp()
        tmp_sub_dirs = {}

        # create temp directory for each service
        for k, v in data.iteritems():
            if v: tmp_sub_dirs[k] = tempfile.mktemp(dir=temp_root_dir)

        # copy config file to temp directories and inject them
        for k, v in tmp_sub_dirs.iteritems():
            p = os.path.join(conf_path, k)
            shutil.copytree(p, v)
            if k == "idp":
                self.inject_idp(v, data.get("idp", {}))
            else if k == "ldap":
                pass # TODO

    def execute(self):
        executable = "/usr/bin/local/docker-compose"
        args = ("up", "--build", "-d")
        path = git.Repo(__file__, search_parent_directories=True)
        path = path.git.rev_parse("--show-toplevel")
        path = os.path.join(path, "docker-shibboleth")

        proc = subprocess.Popen(['ping 8.8.8.8'], shell=True, stdout=\
                subprocess.PIPE)

        for line in iter(proc.stdout.readline, ''):
            time.sleep(1)
            yield line.rstrip()

    def stream_template(self, **context):
        app.update_template_context(context)
        t = app.jinja_env.get_template(self.get_template_name())
        rv = t.stream(context)
        rv.disable_buffering()
        return rv

    def dispatch_request(self):
        # if self.is_locked():
        #    flash("Não autorizado.")
        #    return redirect(url_for("serviceview"))
        return Response(self.stream_template(output=stream_with_context(self.execute())))

# class SSHView(CustomView):
#
#     def test_ssh(self, ip, priv_key, port=22):
#         client = SSHClient()
#         client.set_missing_host_key_policy(AutoAddPolicy())
#         try:
#             client.connect(ip, port=port, username="root", pkey=\
#                     RSAKey.from_private_key(StringIO(priv_key)))
#             return True
#         except:
#             return False
#
#     def dispatch_request(self):
#         if self.is_locked():
#             flash("Não autorizado.")
#             return redirect(url_for("serviceview"))
#         if request.method == "GET":
#             if session['ssh']:
#                 priv_key = session['ssh'].get("priv")
#                 pub_key = session['ssh'].get("pub")
#             else:
#                 priv_key, pub_key = generate_rsa_key()
#                 session['ssh'] = {"pub": pub_key, "priv": priv_key}
#             return self.render_template({"key": pub_key, "ips": session['ssh_ips']})
#
#         if request.method == "POST":
#             ips = {"ldap": None, "sp": None, "idp": None}
#             for k, v in session['data'].iteritems():
#                 if k in ips.keys() and session['data'].get(k, None):
#                     ips[k] = session['data'].get(k).get("ip", None)
#             tmp = ips.copy()
#             for k, v in tmp.iteritems(): # TODO: refactor
#                 if v:
#                     if self.test_ssh(v, \
#                             session['ssh'].get("priv", "")):
#                         ips.pop(k)
#             if len(ips) == 0 and not all(ips.values()):
#                 return redirect(url_for("processview"))
#             else:
#                 for k, v in ips.iteritems():
#                     if v:
#                         flash("Erro ao acessar o %s no IP %s" % (k, v))
#                 return self.render_template({"key": session['ssh'].get("pub"),
#                     "ips": session['ssh_ips']})
#
