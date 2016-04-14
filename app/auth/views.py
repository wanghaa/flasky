from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, login_required, current_user
from . import auth
from .forms import LoginForm, RegistionForm, ChangePasswordForm
from ..models import User
from ..email import send_email
from .. import db


@auth.before_app_request
def before_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.endpoint[:5] != 'auth.' \
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            flash('密码修改成功')
            return redirect(url_for('main.index'))
        else:
            flash('原始密码不正确，请重试')
    return render_template('auth/change_password.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistionForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, '账户确认', 'auth/email/confirm', user=user, token=token)
        flash('确认账户邮件已发送到您的邮箱')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('恭喜你，邮箱验证成功！')
    else:
        flash('验证链接无效')
    return redirect('main.index')


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '确认你的帐户', 'auth/email/confirm', user=current_user, token=token)
    flash('确认邮件已发送到你的邮箱')
    return redirect(url_for('main.index'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('无效的用户名或者密码')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    login_user()
    flash('已退出登录')
    return redirect(url_for('main.index'))
