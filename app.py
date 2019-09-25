from flask import Flask, url_for
from flask import render_template, redirect, flash, request, Markup
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_login import logout_user
from flask_login import login_required
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

from flask_login import current_user, login_user
from models import User, CTFSubSystems
from forms import LoginForm, RegistrationForm, CTFSubsystemForm, ClaimSubsystemForm, EditUserForm, ResetPasswordForm


@app.route('/')
def main_page():
    title = "Home"
    return render_template('index.html', pagetitle=title, user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main_page'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main_page'))
    return render_template('login.html', title='Sign In', form=form, user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main_page'))


@app.route('/user', )
@login_required
def user_details():
    return render_template("user.html", title="User Details", user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main_page'))
    form = RegistrationForm()
    if form.validate_on_submit():
        print("test")
        user = User(name=form.name.data, username=form.username.data, email=form.email.data, current_score=0,
                    is_administrator=False)
        print(user)
        user.set_password(form.password.data)
        db.session.add(user)

        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form, user=current_user)


@app.route('/registersubsystem', methods=['GET', 'POST'])
@login_required
def registerCTFSubsystem():
    form = CTFSubsystemForm()
    if form.validate_on_submit():
        newSubSystem = CTFSubSystems(title=form.title.data, description=form.description.data, score=form.score.data,
                                     Owner="None")
        db.session.add(newSubSystem)
        db.session.commit()
        flash('Congratulations, you have registered a new CTF Subsystem!')
        return redirect(url_for('login'))
    return render_template('registersubsystem.html', title='Register Sub System', form=form, user=current_user)


@app.route('/claimsubsystem', methods=['GET', 'POST'])
@login_required
def claimsubsystem():
    form = ClaimSubsystemForm()
    if form.validate_on_submit():
        print("submit")
        selected_subsystem = request.form.getlist("CTFSubSystems")
        print(selected_subsystem)

        for claimedsubsystems in selected_subsystem:
            claim_new_subsystem = Order(current_user.id, claimedsubsystems)
            db.session.add(claim_new_subsystem)
            flash("Ordered Product: {}".format(claim_new_subsystem.subsystemid))

        print("commit")
        db.session.commit()
        if len(selected_subsystem) > 0:
            flash("Subsystem Claimed")
        else:
            flash("Nothing selected. Please select one or more Subsystems to claim.")
        return redirect(url_for('main_page'))

    subsystems = text('select * from ctf_sub_systems')
    result = db.engine.execute(subsystems)

    return render_template('claim.html', pagetitle='Claim a Subsystem.', products=result, user=current_user, form=form)


@app.route('/edit_user/<userid>', methods=['GET', 'POST'])
@login_required
def edit_User(userid):
    form = EditUserForm()
    user = User.query.filter_by(id=userid).first()
    if form.validate_on_submit():
        user.update_details(form.username.data, form.name.data, form.email.data)
        db.session.commit()
        print("User Updated : {}".format(user))
        flash("User Reset")
        return redirect(url_for('main_page'))

    form.username.data = user.username
    form.email.data = user.email
    form.name.data = user.name
    return render_template('edit-user.html', title='Reset Password', form=form, user=user)


@app.route('/report/listallusers')
def display_users():
    sql = text('select username, id from user')
    result = db.engine.execute(sql)
    users = []
    html_output = Markup(
        "<div class=\"container-fluid table table-hover text-centered\"><div class = \"row\"><div class=\"col-sm-3 "
        "font-weight-bold\">ID</div><div class=\"col-sm-3 font-weight-bold\">User Name</div><div class=\"col-sm-3 "
        "font-weight-bold\">Reset Password</div><div class=\"col-sm-3 font-weight-bold\">Edit User "
        "Details</div></div>")
    for row in result:
        users.append(row)
    print(users)
    user_counter = 1
    for index, user in enumerate(users):

        if index % 2 == 0:
            html_output = Markup(
                "{}<div class = \"row cell1\"><div class=\"col-sm-3\">{}</div> <div class=\"col-sm-3\">{}</div><div "
                "class=\"col-sm-3\"><a href=\"/reset_password/{}\">Reset Password</a></div> <div "
                "class=\"col-sm-3\"><a href=\"/edit_user/{}\">Edit User Details</a></div></div>".format(
                    html_output, user_counter, user[0], user[1], user[1]))
        else:
            html_output = Markup(
                "{}<div class = \"row cell2\"><div class=\"col-sm-3\">{}</div> <div class=\"col-sm-3\">{}</div><div "
                "class=\"col-sm-3\"><a href=\"/reset_password/{}\">Reset Password</a></div><div class=\"col-sm-3\"><a "
                "href=\"/edit_user/{}\">Edit User Details</a></div></div>".format(
                    html_output, user_counter, user[0], user[1], user[1]))
        user_counter = user_counter + 1

    html_output = Markup("{}</tbody></table>".format(html_output))
    print(html_output)

    return render_template('reportresult.html', Title='List of Users', data=html_output, user=current_user)


if __name__ == '__main__':
    app.run()


@app.route('/report/u_ranked')
@login_required
def ranked_users():
    ranked = text('select id, username, current_score from user')
    result = db.engine.execute(ranked)
    users = []
    html_output = Markup(
        "<div class=\"container-fluid table table-hover text-centered\"><div class = \"row\"><div class=\"col-sm-4 "
        "font-weight-bold\">ID</div><div class=\"col-sm-4 font-weight-bold\">Username</div><div class=\"col-sm-4 "
        "font-weight-bold\">Current Score</div></div> "
    )

    for row in result:
        users.append(row)
    print(users)
    # user_counter = 1
    for index, user in enumerate(users):

        if index % 2 == 0:
            html_output = Markup("{}<div class = \"row cell1\"><div class=\"col-sm-4\">{}</div> "
                                 "<div class=\"col-sm-4\">{}</div><div class=\"col-sm-4\">{}</div>"
                                 "</div>".format(html_output, user[0], user[1], user[2]))
        else:
            html_output = Markup(
                "{}<div class = \"row cell2\"><div class=\"col-sm-4\">{}</div> <div class=\"col-sm-4\">{}"
                "</div><div class=\"col-sm-4\">{}</div></div>".format(html_output, user[0], user[1], user[2]))
        # user_counter = user_counter + 1

    html_output = Markup("{}</tbody><table>".format(html_output))
    print(html_output)

    return render_template("reportresult.html", Title="Users Ranked", data=html_output, user=current_user)


@app.route('/reset_password/<userid>', methods=['GET', 'POST'])
@login_required
def reset_user_password(userid):
    form = ResetPasswordForm()
    user = User.query.filter_by(id=userid).first()
    if form.validate_on_submit():
        print("Resetting Password:{}".format(form.new_password.data))

        user.set_password(form.new_password.data)
        db.session.commit()
        print("done")
        flash('Password has been reset for user {}'.format(user.username))
        return redirect(url_for('main_page'))

    return render_template('reset-password.html', title='Reset Password', form=form, user=user)
