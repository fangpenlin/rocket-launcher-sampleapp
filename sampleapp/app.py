from bugsnag.flask import handle_exceptions
from flask import abort
from flask import Flask
from flask import render_template
from flask import Response
from flask_admin import Admin

from . import commands
from .blueprints import public
from .extensions import bcrypt
from .extensions import csrf_protect
from .extensions import db
from .extensions import debug_toolbar
from .extensions import login_manager
from .extensions import mail
from .extensions import migrate
from .models.accounts import User
from .settings import DEFAULT_SECRET_KEY
from .settings import ProdConfig


def create_app(config_object=ProdConfig):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split(".")[0])
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    register_template_filters(app)
    register_admin_views(app)
    register_secret_key_check(app)

    login_manager.login_view = "public.login"
    login_manager.login_message_category = "info"
    return app


def register_extensions(app):
    """Register Flask extensions."""

    bcrypt.init_app(app)
    db.init_app(app)
    csrf_protect.init_app(app)
    debug_toolbar.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    handle_exceptions(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, "code", 500)
        return render_template("{0}.html".format(error_code)), error_code

    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""

    def shell_context():
        """Shell context objects."""
        return {
            "db": db,
            # TODO:
        }

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)


def register_secret_key_check(app):
    def check_secret_key():
        # ensure SECRET_KEY is set properly
        if not app.debug:
            if app.config["SECRET_KEY"] == DEFAULT_SECRET_KEY:
                abort(Response("SECRET_KEY cannot be default value", 500))
            if len(app.config["SECRET_KEY"]) < 32:
                abort(Response("SECRET_KEY too short", 500))

    app.before_request(check_secret_key)


def register_template_filters(app):
    """Register Flask filters."""
    # TODO: add filters here

    # XXX:
    from flask_admin import helpers
    from flask_admin import babel

    app.jinja_env.globals["_gettext"] = babel.gettext
    app.jinja_env.globals["_ngettext"] = babel.ngettext
    app.jinja_env.globals["h"] = helpers

    return None


def register_admin_views(app):
    import flask_admin.consts
    from .admin import ProtectedAdminIndexView
    from .admin import UserModelView

    app.config["FLASK_ADMIN_SWATCH"] = "cerulean"
    url_prefix = app.config["ADMIN_DASHBOARD_PREFIX"]
    admin = Admin(
        app,
        index_view=ProtectedAdminIndexView(url=url_prefix),
        url=url_prefix,
        template_mode="bootstrap3",
    )

    admin.add_view(
        UserModelView(
            User,
            db.session,
            url=f"{url_prefix}/user",
            endpoint="admin.user",
            menu_icon_type=flask_admin.consts.ICON_TYPE_FONT_AWESOME,
            menu_icon_value="user",
        ),
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
