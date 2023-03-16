from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_babel import _
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.auth.email import send_password_reset_email
import pyotp
import sys

# 2FA page route
@bp.route("/login/2fa/<int:id>")
def login_2fa(id):
    return render_template("auth/login_2fac.html", id=id)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('auth.login'))
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('auth.login_2fa', id = user.id)
        return redirect(url_for('auth.login_2fa', id = user.id))
    return render_template('auth/login.html', title=_('Sign In'), form=form)


@bp.route("/login/2fa/<int:id>", methods=["POST"])
def login_2fa_form(id):
    user = User.query.get(id)
    secret = user.FA_token
    otp = request.form.get("otp")
    if pyotp.TOTP(secret).verify(otp):
        login_user(user)
        flash("The TOTP 2FA token is valid", "success")
        return redirect(url_for("main.index"))
    else:
        flash("You have supplied an invalid 2FA token!", "danger")
        return redirect(url_for("auth.login_2fa",  id=id)) 

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        secret = pyotp.random_base32()
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        user.set_two_FA(secret)
        db.session.add(user)
        db.session.commit()
        flash(_(f'Congratulations, you are now a registered user!'))
        return render_template('auth/secret_key.html', secret=secret)
    return render_template('auth/register.html', title=_('Register'),
                           form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title=_('Reset Password'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
