from flask import Blueprint, render_template

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(404)
def error_404(error):
    return render_template('error.html', error_info=error, error_code=404), 404


@errors.app_errorhandler(403)
def error_403(error):
    return render_template('error.html', error_info=error, error_code=403), 403


@errors.app_errorhandler(500)
def error_500(error):
    return render_template('error.html', error_info=error, error_code=500), 500
