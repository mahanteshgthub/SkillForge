from flask import Flask, render_template, redirect, url_for, flash, request
from config import Config
from forms import LoginForm, RegistrationForm
from models import db, User
from forms import RegistrationForm, LoginForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from admin.routes import admin_bp
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db

app = Flask(__name__) 
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///E:/SkillForge/skillforge.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skillforge.db'
app.config['REMEMBER_COOKIE_DURATION'] = 0  # Disable remember me functionality
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Prevent cached static files during dev
# from admin.models import WorkorderTemplate
from trainer.routes import trainer_bp

login_manager = LoginManager(app)
login_manager.login_view = "login"
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(trainer_bp)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/") 
@app.route('/')
def home():
    form = LoginForm()
    return render_template('home.html', form=form)

@app.route('/start')
def start():
    return render_template('welcome.html')

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered. Please try with a different one!", "warning")
        else:
            new_user = User(
                name=form.name.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data),
                role=form.role.data,
                status="pending"  # New users have a 'pending' status by default
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Registration submitted. Awaiting admin approval.", "info")
            return redirect(url_for("home"))

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            if user.status == "approved":
                login_user(user,remember=False)
                return redirect(url_for("dashboard"))
            else:
                flash(f"Your account is {user.status}. Contact admin.", "danger")
        else:
            flash("Invalid email or password.", "danger")

    return render_template("home.html", form=form)

@app.route("/auto-logout", methods=["POST"])
@login_required
def auto_logout():
    logout_user()
    return '', 204  # No content

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin():
        pending_users = User.query.filter_by(status="pending").all()
        all_users = User.query.filter(User.role != "Admin").all()
        return render_template("admin_dashboard.html", pending=pending_users, users=all_users)

    elif current_user.is_trainer():
        return redirect(url_for("trainer.trainer_dashboard"))

    else:
        return render_template("trainee_dashboard.html")
    
@app.route("/admin/<int:user_id>/<action>")
@login_required
def admin_action(user_id, action):
    if not current_user.is_admin():
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(user_id)
    if action == "approve":
        user.status = "approved"
    elif action == "reject":
        user.status = "rejected"
    elif action == "block":
        user.status = "blocked"
    elif action == "delete":
        db.session.delete(user)
        db.session.commit()
        flash("User deleted.", "info")
        return redirect(url_for("dashboard"))

    db.session.commit()
    flash(f"User {action}d successfully.", "success")
    return redirect(url_for("dashboard"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

def setup_app():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email="bhadrannavar.mahantesh@gmail.com").first():
            admin = User(
                name="Mahantesh",
                email="bhadrannavar.mahantesh@gmail.com",
                password=generate_password_hash("AdminPass123"),
                role="Admin",
                status="approved"
            )
            db.session.add(admin)
            db.session.commit()

if __name__ == "__main__":
    setup_app()
    app.run(debug=True)

from functools import wraps
from flask import abort
from flask_login import current_user

def trainer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['trainer', 'admin']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/trainer/dashboard')
@trainer_required
def trainer_dashboard():
    return render_template('trainer_dashboard.html')
