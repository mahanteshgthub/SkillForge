from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class RegistrationForm(FlaskForm):
    name     = StringField("Full Name", validators=[DataRequired(), Length(min=2)])

    email    = StringField("Email", validators=[DataRequired(), Email()])

    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])

    confirm  = PasswordField("Confirm Password",
        validators=[DataRequired(), EqualTo("password")])

    role     = SelectField("Enroll as",
        choices=[("Trainer", "Trainer"), ("Trainee", "Trainee")],
        validators=[DataRequired()])

    submit   = SubmitField("Register")

class LoginForm(FlaskForm):
    email    = StringField("Email", validators=[DataRequired(), Email()])

    password = PasswordField("Password", validators=[DataRequired()])

    submit   = SubmitField("Log In")

class SetupUnitForm(FlaskForm):
    iti_name = StringField("ITI Name", validators=[DataRequired()])
    city = StringField("City / Town / Village", validators=[DataRequired()])
    iti_code = StringField("ITI Code", validators=[DataRequired(), Length(min=10, max=10)])
    trade = SelectField("Trade", choices=[
        ("Fitter", "Fitter"),
        ("DMM", "DMM"),
        ("DMC", "DMC"),
        ("Welder", "Welder"),
        ("E/M", "E/M"),
        ("Turner", "Turner"),
        ("Electrician", "Electrician"),
        ("Diesel Mech", "Diesel Mech"),
        ("MMV", "MMV")
    ], validators=[DataRequired()])
    shift_number = SelectField("Shift", choices=[("1", "1"), ("2", "2")], validators=[DataRequired()])
    unit_number = SelectField("Unit Number", choices=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")], validators=[DataRequired()])
    
    year_of_admission = SelectField(
    "Year of Admission",
    choices=[(str(y), str(y)) for y in range(2020, 2051)],
    validators=[Optional()]  # Or omit validator since it's nullable
        )

    year = SelectField("Year", choices=[("Jr", "Junior"), ("Sr", "Senior")], validators=[DataRequired()])
    submit = SubmitField("Save Setup")


from wtforms import StringField, SelectField
from wtforms.validators import DataRequired

class TraineeForm(FlaskForm):
    trainee_name = StringField('Name', validators=[DataRequired()])
    grade = SelectField(
        'Grade',
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        validators=[DataRequired()]
    )

    class Meta:
        csrf = False  # Disable CSRF for embedded subform

class TraineeListForm(FlaskForm):
    trainees = FieldList(FormField(TraineeForm), min_entries=0)
