from flask_sqlalchemy import SQLAlchemy # Provides SQLAlchemy ORM integration for Flask
from flask_login import UserMixin # Provides default implementations for Flask-Login user methods

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)

    name     = db.Column(db.String(100), nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role     = db.Column(db.String(20), nullable=False)  # 'Admin','Trainer','Trainee'
    status   = db.Column(db.String(20), default="pending")

    def is_admin(self):
        return self.role == "Admin"

    def is_trainer(self):
        return self.role == "Trainer"

    def is_trainee(self):
        return self.role == "Trainee"

# from models import db
class WorkorderTemplate(db.Model):
    __tablename__ = 'workorder_template'
    __table_args__ = (
        db.UniqueConstraint('trade', 'year', 'exercise_no', 'job_image', name='uq_trade_year_exercise_aim'),
    )
    id = db.Column(db.Integer, primary_key=True)
    trade = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(10), nullable=False)  # e.g., Jr or Sr
    exercise_no = db.Column(db.String(2), nullable=False)
    aim = db.Column(db.String(255), nullable=False)
    job_image = db.Column(db.String(255), nullable=True) 
    common_tolerance = db.Column(db.String(20), nullable=False)
    job_image = db.Column(db.String(255)) 
    dimensional_features = db.relationship('DimensionalFeature', backref='workorder', lazy=True)
    subjective_features = db.relationship('SubjectiveFeature', backref='workorder', lazy=True)
    attitude_features = db.relationship('AttitudeFeature', backref='workorder', lazy=True)
class DimensionalFeature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(2))
    size = db.Column(db.String(50))
    marks = db.Column(db.Integer)
    workorder_id = db.Column(db.Integer, db.ForeignKey('workorder_template.id'))
class SubjectiveFeature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(2))
    operation = db.Column(db.String(100))
    marks = db.Column(db.Integer)
    workorder_id = db.Column(db.Integer, db.ForeignKey('workorder_template.id'))
class AttitudeFeature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(2))
    trait = db.Column(db.String(100))
    marks = db.Column(db.Integer)
    workorder_id = db.Column(db.Integer, db.ForeignKey('workorder_template.id'))

class JobItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    category = db.Column(db.String(50), nullable=False)  # e.g., 'instrument', 'tool', etc.
    name = db.Column(db.String(100), nullable=False)
    def __repr__(self):
        return f"<JobItem {self.category}: {self.name}>"

class JobInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trade = db.Column(db.String(50), nullable=False)
    year = db.Column(db.String(10))  # Or Enum('Jr', 'Sr') if you want to constrain it
    ex_no = db.Column(db.String(5))  # "Ex-01", "1A", etc.
    aim = db.Column(db.Text, nullable=False)
    material = db.Column(db.String(200))
    stock_size = db.Column(db.String(100))
    time = db.Column(db.Float)
    instruments = db.Column(db.Text)
    tools = db.Column(db.Text)
    devices = db.Column(db.Text)
    equipment = db.Column(db.Text)
    operations = db.Column(db.Text)
    other_items = db.Column(db.Text)

    workorder_id = db.Column(db.Integer, db.ForeignKey('workorder_template.id'))
    workorder = db.relationship("WorkorderTemplate", backref="job_infos")
    
class TrainerUnit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trainer_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    iti_name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    iti_code = db.Column(db.String(10), nullable=False)
    trade = db.Column(db.String(50), nullable=False)
    shift_number = db.Column(db.Integer, nullable=False)
    unit_number = db.Column(db.Integer, nullable=False)
    year = db.Column(db.String(10), nullable=False)
    year_of_admission = db.Column(db.Integer, nullable=True)
      
    trainer = db.relationship("User", backref="unit_profile", uselist=False)
    trainees = db.relationship(
        "Trainee",
        backref="trainer_unit",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class Trainee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trainer_unit_id = db.Column(db.Integer, db.ForeignKey('trainer_unit.id', ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    grade = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f"<Trainee {self.name} - Grade {self.grade}>"  