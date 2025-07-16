from models import db
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