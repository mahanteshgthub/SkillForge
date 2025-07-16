from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from decorators import trainer_required
from models import TrainerUnit, Trainee, db, JobInfo
from forms import SetupUnitForm, TraineeListForm, TraineeForm
from flask import make_response
from models import WorkorderTemplate
# from models import TrainerUnit  # TrainerUnit is defined in your main models
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import joinedload

# job_infos = JobInfo.query \
#     .options(joinedload(JobInfo.workorder)) \
#     .filter_by(trade=unit.trade, year=unit.year) \
#     .all()

import io
from flask import send_file, current_app
import tempfile, os
from models import Trainee  # Assuming this is your trainee model

# from utils.excel_utils import fill_excel_template, convert_excel_to_pdf_silent  # adjust path if needed

from utils.excel_writer import fill_excel_template
from utils.pdf_converter import convert_excel_to_pdf_silent


# Create a Blueprint for the trainer routes
trainer_bp = Blueprint('trainer', __name__, url_prefix='/trainer')


@trainer_bp.route('/upload', methods=['GET', 'POST'])
@trainer_required
def upload_material():
    return render_template('trainer_upload.html')

@trainer_bp.route('/feedback')
@trainer_required
def view_feedback():
    return render_template('trainer_feedback.html')

# Trainer Blueprint for handling trainer-specific routes
@trainer_bp.route("/setup", methods=["GET", "POST"])
@login_required
@trainer_required
def setup_unit():
    unit = TrainerUnit.query.filter_by(trainer_id=current_user.id).first()
    form = SetupUnitForm(obj=unit)

    is_edit_mode = request.args.get("edit") == "true"
    if not unit:
        is_edit_mode = True

    if form.validate_on_submit():
        if unit:
            form.populate_obj(unit)
        else:
            unit = TrainerUnit(
                trainer_id=current_user.id,
                iti_name=form.iti_name.data,
                city=form.city.data,
                iti_code=form.iti_code.data,
                trade=form.trade.data,
                shift_number=form.shift_number.data,
                unit_number=form.unit_number.data,
                year=form.year.data,
                year_of_admission=int(form.year_of_admission.data) if form.year_of_admission.data else None
            )
            db.session.add(unit)

        db.session.commit()
        flash("Your unit details have been saved successfully!", "success")
        return redirect(url_for("trainer.setup_unit"))

    # ✅ Always render the correct template
    return render_template("trainer_setup.html", form=form, unit=unit, is_edit_mode=is_edit_mode)


@trainer_bp.route("/dashboard")
@login_required
@trainer_required
def trainer_dashboard():
    unit = TrainerUnit.query.filter_by(trainer_id=current_user.id).first()
    trainee_count = len(unit.trainees) if unit and unit.trainees else 0
    return render_template("trainer_dashboard.html", unit=unit, trainee_count=trainee_count)

@trainer_bp.route('/trainees', methods=['GET', 'POST'])
@login_required
@trainer_required
def manage_trainees():
    unit = TrainerUnit.query.filter_by(trainer_id=current_user.id).first()
    if not unit:
        flash("Please complete your unit setup first.", "warning")
        return redirect(url_for('trainer.setup_unit'))

    form = TraineeListForm()

    if request.method == 'GET':
        form.trainees.entries = []

        if unit.trainees:
            for trainee in unit.trainees:
                subform = form.trainees.append_entry()
                subform.trainee_name.data = str(trainee.name)
                subform.grade.data = str(trainee.grade)
        else:
            for _ in range(3):
                form.trainees.append_entry()

    if form.validate_on_submit():
        # Clean old data
        Trainee.query.filter_by(trainer_unit_id=unit.id).delete()

        # Add new trainee records
        for trainee_form in form.trainees:
            trainee = Trainee(
                name=trainee_form.trainee_name.data.strip(),
                grade=trainee_form.grade.data.strip(),
                trainer_unit_id=unit.id
            )
            db.session.add(trainee)

        db.session.commit()

        # Debug confirmation
        print("✅ Saved trainees:")
        for idx, trainee_form in enumerate(form.trainees, 1):
            print(f"  {idx}: {trainee_form.trainee_name.data} ({trainee_form.grade.data})")

        flash("Trainee list saved successfully ✅", "success")
        return redirect(url_for('trainer.manage_trainees'))

    elif request.method == 'POST':
        # Form submitted but didn't pass validation
        print("❌ Form did not validate.")
        print("Form errors:", form.errors)

    # Final fallback render
    return render_template('trainer_trainees.html', form=form)

@trainer_bp.route("/workorders")
@login_required
@trainer_required
def view_workorders():
    unit = TrainerUnit.query.filter_by(trainer_id=current_user.id).first()
    if not unit:
        flash("Please complete your unit setup first.", "warning")
        return redirect(url_for("trainer.setup_unit"))

    workorders = WorkorderTemplate.query.filter_by(
        trade=unit.trade,
        year=unit.year
    ).order_by(WorkorderTemplate.exercise_no).all()

    return render_template("trainer/workorder_list.html", templates=workorders)



# @trainer_bp.route('/workorders/export/<int:workorder_id>/pdf')
# @trainer_bp.route('/workorders/export/<int:workorder_id>/pdf', methods=['POST'])
@trainer_bp.route('/workorders/export/<int:workorder_id>/pdf', methods=['GET', 'POST'])
@login_required
@trainer_required
def export_pdf(workorder_id):
    work = WorkorderTemplate.query.get_or_404(workorder_id)

    # ✅ Get the trainer's unit
    unit = TrainerUnit.query.filter_by(trainer_id=current_user.id).first()

    # ✅ Corrected: Fetch trainees linked to this unit
    trainees = Trainee.query.filter_by(trainer_unit_id=unit.id).all()

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        filled_path = tmp.name

    print("Trainees:", [(t.name, t.grade) for t in trainees])  # Debug print

        # 📥 Get values from the form
    override_ex = request.form.get("override_exercise")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    # ⛳ Override exercise number only for export—not saved in DB
    if override_ex and override_ex.isdigit():
        work.exercise_no = str(override_ex)

    # 📅 Date formatting logic
    from datetime import datetime
    def format_date(date_str):
        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d")
            return parsed.strftime("%d.%m.%Y")  # Change to "%d-%m-%Y" if you prefer
        except:
            return None

    dates = {}

    formatted_start = format_date(start_date)
    if formatted_start:
        dates["start"] = formatted_start

    formatted_end = format_date(end_date)
    if formatted_end:
        dates["end"] = formatted_end

    # 🚀 Pass formatted data to template
    fill_excel_template(work, filled_path, trainees=trainees, unit=unit, dates=dates)    
    pdf_path = os.path.join(current_app.root_path, 'static', 'reports', f'workorder_{work.id}_trainer.pdf')
    convert_excel_to_pdf_silent(filled_path, pdf_path)
    os.remove(filled_path)
   
    return send_file(pdf_path, as_attachment=False)

@trainer_bp.route('/job-info-list', methods=['GET'])
@login_required
@trainer_required
def job_info_list():
    unit = TrainerUnit.query.filter_by(trainer_id=current_user.id).first()
    if not unit:
        flash("Trainer unit info not found.", "warning")
        return redirect(url_for("trainer.dashboard"))

    job_infos = JobInfo.query \
        .options(db.joinedload(JobInfo.workorder)) \
        .filter_by(trade=unit.trade, year=unit.year) \
        .all()

    return render_template("trainer/job_info_list.html", job_infos=job_infos)