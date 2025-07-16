# Import necessary classes from Flask-WTF and WTForms
from flask_wtf import FlaskForm # Base class for creating web forms with Flask-WTF
from wtforms import StringField, TextAreaField, FileField, SubmitField, IntegerField, FieldList, FormField # Various field types for forms
from wtforms.validators import DataRequired, Optional, NumberRange # Validators for input data
from flask_wtf.file import FileAllowed # Validator specifically for file uploads
from wtforms import Form # Import base Form class for creating nested forms (forms within forms)
from wtforms import SelectField # Field type for dropdown selection
from wtforms.validators import ValidationError # Used to raise custom validation errors
from models import WorkorderTemplate # Import WorkorderTemplate model for database interaction in validation

# Define a nested form for Dimensional Features.
# This form represents a single dimensional feature within a workorder.
class DimFeatureForm(Form):
    # 'label' field: A string field for the label (e.g., A, B, C).
    # This might be dynamically assigned or pre-filled in the template.
    label = StringField("Label")

    # 'size' field: A string field for the size of the feature.
    # Optional(): Means this field doesn't have to be filled.
    size = StringField("Size", validators=[Optional()])

    # 'marks' field: An integer field for marks associated with the feature.
    # Optional(): Means this field doesn't have to be filled.
    marks = IntegerField("Marks", validators=[Optional()])

# Define a nested form for Subjective Features.
# This form represents a single subjective feature within a workorder.
class SubjFeatureForm(Form):
    # 'label' field: A string field for the label (e.g., K, L, M).
    label = StringField("Label")

    # 'operation' field: A string field describing the subjective feature or operation.
    # Optional(): Means this field doesn't have to be filled.
    operation = StringField("Feature", validators=[Optional()])

    # 'marks' field: An integer field for marks associated with the feature.
    # Optional(): Means this field doesn't have to be filled.
    marks = IntegerField("Marks", validators=[Optional()])

# Define a nested form for Attitude Features.
# This form represents a single attitude feature within a workorder.
class AttFeatureForm(Form):
    # 'label' field: A string field for the label (e.g., P, Q, R).
    label = StringField("Label")

    # 'trait' field: A string field describing the attitude trait.
    # Optional(): Means this field doesn't have to be filled.
    trait = StringField("Trait", validators=[Optional()])

    # 'marks' field: An integer field for marks associated with the feature.
    # Optional(): Means this field doesn't have to be filled.
    marks = IntegerField("Marks", validators=[Optional()])

# Define the main WorkorderForm class, inheriting from FlaskForm.
# This form is used to create or edit a complete workorder.
class WorkorderForm(FlaskForm):
    # 'trade' field: A string field for the trade associated with the workorder.
    # DataRequired(): Ensures this field is not empty.
    trade = StringField("Trade", validators=[DataRequired()])

    # 'year' field: A dropdown select field for the year (Jr or Sr).
    # choices: Defines the options for the dropdown (value, display text).
    year = SelectField('Year', choices=[('Jr', 'Jr'), ('Sr', 'Sr')])

    # 'exercise_no' field: A dropdown select field for the exercise number.
    # choices: Dynamically generates numbers from 1 to 52 for the dropdown.
    exercise_no = SelectField('Exercise No.', choices=[(str(i), f'{i}') for i in range(1, 53)])

    # 'aim' field: A multi-line text area for the aim of the workorder.
    # DataRequired(): Ensures this field is not empty.
    aim = TextAreaField("Aim", validators=[DataRequired()])

    # 'common_tolerance' field: A string field for common dimensional tolerance.
    # DataRequired(): Ensures this field is not empty.
    common_tolerance = StringField("Common Dimensional Tolerance", validators=[DataRequired()])

    # 'job_image' field: A file upload field for the job image.
    # FileAllowed(['jpg', 'jpeg', 'png']): Validator to ensure only specified image types are uploaded.
    job_image = FileField("Job Image", validators=[FileAllowed(['jpg', 'jpeg', 'png'])])

    # 'dim_features' field: A list of Dimensional Feature forms.
    # FieldList(FormField(DimFeatureForm)): Allows multiple instances of DimFeatureForm to be submitted.
    # min_entries=10: Ensures at least 10 Dimensional Feature entries are present (can be empty but must exist in the list).
    dim_features = FieldList(FormField(DimFeatureForm), min_entries=10)

    # 'subj_features' field: A list of Subjective Feature forms.
    # min_entries=5: Ensures at least 5 Subjective Feature entries.
    subj_features = FieldList(FormField(SubjFeatureForm), min_entries=5)

    # 'attitude_features' field: A list of Attitude Feature forms.
    # min_entries=4: Ensures at least 4 Attitude Feature entries.
    attitude_features = FieldList(FormField(AttFeatureForm), min_entries=4)

    # 'submit' field: A submit button for the form.
    # "Create Workorder": Text displayed on the button.
    submit = SubmitField("Create Workorder")

    # Custom validation method for the 'aim' field.
    # This method is automatically called by WTForms when validate_on_submit() is used.
    def validate_aim(self, field):
        # Import WorkorderTemplate model within the method to avoid circular imports if models depends on forms.
        # This is a common pattern when models are used in form validation.
        # from admin.models import WorkorderTemplate

        # Query the database to check if a WorkorderTemplate with the same
        # trade, year, exercise_no, and job_image already exists.
        existing = WorkorderTemplate.query.filter_by(
            trade=self.trade.data, # Get data from the 'trade' field
            year=self.year.data,   # Get data from the 'year' field
            exercise_no=self.exercise_no.data, # Get data from the 'exercise_no' field
            # Get the filename of the uploaded job image; if no image, set to None.
            job_image=self.job_image.data.filename if self.job_image.data else None
        ).first() # Retrieve the first matching record, if any.

        # If an existing work order is found with these matching criteria, raise a validation error.
        if existing:
            raise ValidationError("A Work Order with this Trade, Year, Exercise No., and Job Image already exists.")