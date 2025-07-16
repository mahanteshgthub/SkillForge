import os # Provides functions for interacting with the operating system (e.g., file paths)
from flask import Blueprint, render_template, redirect, flash, url_for, request, current_app # Flask core components
from werkzeug.utils import secure_filename # For securely handling uploaded filenames
from flask_login import login_required, current_user # For managing user sessions and access control
from admin.forms import WorkorderForm # Import the WorkorderForm defined in the current package's forms.py
from models import db, WorkorderTemplate, DimensionalFeature, SubjectiveFeature, AttitudeFeature # Import database models from the current package's models.py
from utils.pdf_generator import generate_workorder_pdf # Utility for generating PDFs (though seems unused directly here)
from flask import send_file # For sending files as responses
from flask import send_file, current_app # Redundant import of send_file, current_app
from utils.excel_writer import fill_excel_template # Utility to fill an Excel template
from utils.pdf_converter import convert_excel_to_pdf_silent # Utility to convert Excel to PDF (if external conversion tool is used)
import tempfile # For creating temporary files
from models import JobItem # Import JobItem model (from the root models.py)
from models import JobInfo # Import JobInfo model (from the root models.py)
from models import TrainerUnit, Trainee, db



admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/design", methods=["GET", "POST"])
@login_required # Requires the user to be logged in to access this route.
def design_workorder():
    if not current_user.is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))
    form = WorkorderForm()
    dim_labels = list("ABCDEFGHIJ")
    subj_labels = list("KLMNO")
    att_labels = list("PQRS")
    default_traits = ["Safety", "House keeping", "Initiative", "Co-operation"]
    for i, field in enumerate(form.attitude_features):
        if not field.trait.data: # If the trait data is not already set (e.g., on a GET request)
            field.trait.data = default_traits[i] # Assign a default trait
        if field.marks.data is None: # If marks data is not set
            field.marks.data = 5 # Assign a default of 5 marks
    validated = form.validate_on_submit()
    print("📥 Method:", request.method) # Shows HTTP method (GET or POST)
    print("📋 form.is_submitted():", form.is_submitted()) # Checks if form was submitted
    print("⚠️  form.errors:", form.errors) # Displays validation errors, if any
    print("✅ validated:", validated) # Shows validation result (True/False)
    if validated:
        from models import WorkorderTemplate
        job_image_filename = secure_filename(form.job_image.data.filename) if form.job_image.data else None
        duplicate = WorkorderTemplate.query.filter_by(
            trade=form.trade.data,
            year=form.year.data,
            exercise_no=form.exercise_no.data,
            job_image=job_image_filename
        ).first()
        if duplicate:
            flash("⚠️ Duplicate Work Order: A workorder with this Trade, Year, Exercise No., and Image already exists.", "warning")
            return render_template("admin/design_form.html", form=form)
        total_marks = 0 # Initialize total marks counter
        for f in form.dim_features:
            if f.marks.data: # Only add if marks data is present
                total_marks += f.marks.data
        for f in form.subj_features:
            if f.marks.data:
                total_marks += f.marks.data
        for f in form.attitude_features:
            if f.marks.data:
                total_marks += f.marks.data

        print("🔢 Total marks calculated:", total_marks)

        if total_marks != 100:
            flash(f"❌ Total marks must be exactly 100. Currently: {total_marks}", "danger")
            return render_template("admin/design_form.html", form=form)

        try:
            filename = None # Initialize filename for the job image
            if form.job_image.data: # If an image was uploaded
                filename = secure_filename(form.job_image.data.filename) # Secure the filename
                # Construct the upload path: static/uploads/filename
                upload_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
                form.job_image.data.save(upload_path) # Save the uploaded file

            new_work = WorkorderTemplate(
                trade=form.trade.data,
                year=form.year.data,
                exercise_no=form.exercise_no.data,
                aim=form.aim.data,
                common_tolerance=form.common_tolerance.data,
                job_image=filename # Store the secured filename in the database
            )
            db.session.add(new_work) # Add the new workorder to the database session
            db.session.flush() # Flush the session to get the 'id' of the new_work for foreign keys

            for i, f in enumerate(form.dim_features):
                if f.size.data or f.marks.data is not None: # Only save if size or marks are provided
                    dim = DimensionalFeature(
                        label=dim_labels[i], # Assign a label (A, B, C...)
                        size=f.size.data,
                        marks=f.marks.data,
                        workorder_id=new_work.id # Link to the newly created workorder
                    )
                    db.session.add(dim) # Add to session

            for i, f in enumerate(form.subj_features):
                if f.operation.data or f.marks.data is not None:
                    subj = SubjectiveFeature(
                        label=subj_labels[i], # Assign a label (K, L, M...)
                        operation=f.operation.data,
                        marks=f.marks.data,
                        workorder_id=new_work.id
                    )
                    db.session.add(subj)

            for i, f in enumerate(form.attitude_features):
                if f.trait.data or f.marks.data is not None:
                    att = AttitudeFeature(
                        label=att_labels[i], # Assign a label (P, Q, R...)
                        trait=f.trait.data,
                        marks=f.marks.data,
                        workorder_id=new_work.id
                    )
                    db.session.add(att)

            db.session.commit() # Commit all changes to the database
            flash("✅ Workorder created successfully!", "success") # Flash success message
            return redirect(url_for("dashboard")) # Redirect to dashboard

        except Exception as e:
            print("❌ ERROR during form submission:", e) # Print error to console for debugging
            flash("Something went wrong while saving. Check server logs.", "danger") # Flash error message to user

    return render_template("admin/design_form.html", form=form)

@admin_bp.route("/workorders")
@login_required # Requires user to be logged in.
def view_workorders():
    # Check if the current user is an admin.
    if not current_user.is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))

    trade_filter = request.args.get("trade", "")
    year_filter = request.args.get("year", "")

    query = WorkorderTemplate.query
    if trade_filter:
        query = query.filter(WorkorderTemplate.trade.ilike(f"%{trade_filter}%"))
    if year_filter:
        query = query.filter_by(year=year_filter)

    workorders = query.order_by(WorkorderTemplate.exercise_no).all()
    return render_template("admin/workorder_list.html", templates=workorders)

@admin_bp.route("/edit/<int:workorder_id>", methods=["GET", "POST"])
@login_required # Requires user to be logged in.
def edit_workorder(workorder_id):
    if not current_user.is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))

    work = WorkorderTemplate.query.get_or_404(workorder_id)
    # Define labels for features (same as in design route).
    dim_labels = list("ABCDEFGHIJ")
    subj_labels = list("KLMNO")
    att_labels = list("PQRS")

    form = WorkorderForm(obj=work)

    if request.method == "GET":
        # Populate dimensional features.
        for i, f in enumerate(form.dim_features):
            if i < len(work.dimensional_features): # Ensure index is within bounds of existing features
                f.size.data = work.dimensional_features[i].size
                f.marks.data = work.dimensional_features[i].marks

        for i, f in enumerate(form.subj_features):
            if i < len(work.subjective_features):
                f.operation.data = work.subjective_features[i].operation
                f.marks.data = work.subjective_features[i].marks

        for i, f in enumerate(form.attitude_features):
            if i < len(work.attitude_features):
                f.trait.data = work.attitude_features[i].trait
                f.marks.data = work.attitude_features[i].marks

    if form.validate_on_submit():
        total_marks = sum(
            (f.marks.data or 0) # Use 0 if marks data is None to avoid errors
            for f in list(form.dim_features) + list(form.subj_features) + list(form.attitude_features)
        )

        if total_marks != 100:
            flash(f"❌ Total marks must be exactly 100. Currently: {total_marks}", "danger")
            # Re-render the form with existing data and error message.
            return render_template("admin/design_form.html", form=form)

        work.trade = form.trade.data
        work.year = form.year.data
        work.exercise_no = form.exercise_no.data
        work.aim = form.aim.data
        work.common_tolerance = form.common_tolerance.data

        if form.job_image.data:
            filename = secure_filename(form.job_image.data.filename)
            path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
            form.job_image.data.save(path)
            work.job_image = filename

        DimensionalFeature.query.filter_by(workorder_id=work.id).delete()
        SubjectiveFeature.query.filter_by(workorder_id=work.id).delete()
        AttitudeFeature.query.filter_by(workorder_id=work.id).delete()

        for i, f in enumerate(form.dim_features):
            if f.size.data or f.marks.data is not None:
                db.session.add(DimensionalFeature(
                    label=dim_labels[i],
                    size=f.size.data,
                    marks=f.marks.data,
                    workorder_id=work.id
                ))
        for i, f in enumerate(form.subj_features):
            if f.operation.data or f.marks.data is not None:
                db.session.add(SubjectiveFeature(
                    label=subj_labels[i],
                    operation=f.operation.data,
                    marks=f.marks.data,
                    workorder_id=work.id
                ))
        for i, f in enumerate(form.attitude_features):
            if f.trait.data or f.marks.data is not None:
                db.session.add(AttitudeFeature(
                    label=att_labels[i],
                    trait=f.trait.data,
                    marks=f.marks.data,
                    workorder_id=work.id
                ))

        db.session.commit() # Commit all changes (updates, deletions, additions) to the database.
        flash("✅ Workorder updated successfully!", "success") # Flash success message.
        return redirect(url_for("admin.view_workorders")) # Redirect to the list of workorders.

    return render_template("admin/design_form.html", form=form)

from flask import send_file
from io import BytesIO
import tempfile
import os


@admin_bp.route('/export/<int:workorder_id>/pdf', methods=['GET', 'POST'])
@login_required
def export_pdf(workorder_id):
    work = WorkorderTemplate.query.get_or_404(workorder_id)

    unit = TrainerUnit.query.filter_by(trainer_id=current_user.id).first()
    
    trainees = Trainee.query.filter_by(trainer_unit_id=unit.id).all() if unit else []

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_excel:
        excel_path = tmp_excel.name

    override_ex = request.form.get("override_exercise")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    from datetime import datetime
    def format_date(date_str):
        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d")
            return parsed.strftime("%d.%m.%Y")  # Change to "%d-%m-%Y" if needed
        except:
            return None

        # ⛳ Use selected exercise number only for export (don't save)
    if override_ex and override_ex.isdigit():
        work.exercise_no = str(override_ex)

    # 🎯 Format start/end dates for Excel export
    dates = {}
    formatted_start = format_date(start_date)
    if formatted_start:
        dates["start"] = formatted_start

    formatted_end = format_date(end_date)
    if formatted_end:
        dates["end"] = formatted_end

    fill_excel_template(work, excel_path, trainees=trainees if trainees else None, unit=unit, dates=dates)
    # fill_excel_template(work, excel_path, trainees=trainees, unit=None, dates=dates)

    # fill_excel_template(work, excel_path, trainees=trainees, unit=unit)

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
        pdf_path = tmp_pdf.name

    convert_excel_to_pdf_silent(excel_path, pdf_path)

    with open(pdf_path, 'rb') as f:
        pdf_bytes = BytesIO(f.read())

    os.remove(excel_path)
    os.remove(pdf_path)

    pdf_bytes.seek(0)
    return send_file(pdf_bytes, mimetype='application/pdf', as_attachment=False)

@admin_bp.route("/delete/<int:workorder_id>", methods=["POST"])
@login_required # Requires user to be logged in.
def delete_workorder(workorder_id):
    if not current_user.is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))

    work = WorkorderTemplate.query.get_or_404(workorder_id)

    DimensionalFeature.query.filter_by(workorder_id=work.id).delete()
    SubjectiveFeature.query.filter_by(workorder_id=work.id).delete()
    AttitudeFeature.query.filter_by(workorder_id=work.id).delete()

    db.session.delete(work) # Delete the WorkorderTemplate itself from the session.
    db.session.commit() # Commit the changes to the database.

    flash("🗑️ Workorder deleted successfully!", "success") # Flash success message.
    return redirect(url_for("admin.view_workorders")) # Redirect to the list of workorders.

@admin_bp.route('/job-info', methods=['GET', 'POST'])
@login_required # Requires user to be logged in.
def job_info_sheet():
    # Check if the current user is an admin.
    if not current_user.is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))

    if request.method == 'POST':
        for cat in ['instrument', 'tool', 'device', 'equipment', 'operation']:
            values = request.form.getlist(cat)
            for name in values: # For each submitted item name
                exists = JobItem.query.filter_by(category=cat, name=name).first()
                if not exists: # If it does not exist, add it.
                    db.session.add(JobItem(category=cat, name=name))

        # Find the matching WorkorderTemplate by trade, year, and exercise_no from the form
        exercise_no = request.form.get('ex_no')  # Make sure this field is present in your form!
        workorder = WorkorderTemplate.query.filter_by(
            trade=request.form.get('trade'),
            year=request.form.get('year'),
            exercise_no=exercise_no
        ).first()

        job = JobInfo(
            trade=request.form.get('trade'), # Get trade from form
            year=request.form.get('year'), # Get year from form
            ex_no=exercise_no, # Get exercise number from form
            aim=request.form.get('aim'), # Get aim from form
            material=request.form.get('material'), # Get material from form
            stock_size=request.form.get('stock_size'), # Get stock size from form
            time=request.form.get('time'), # Get time from form
            # Join lists of items (e.g., instruments, tools) into comma-separated strings for storage.
            instruments=','.join(request.form.getlist('instrument')),
            tools=','.join(request.form.getlist('tool')),
            devices=','.join(request.form.getlist('device')),
            equipment=','.join(request.form.getlist('equipment')),
            operations=','.join(request.form.getlist('operation')),
            other_items=request.form.get('other_items'), # Get other items from form
            workorder_id=workorder.id if workorder else None  # ✅ Link to the workorder
        
        )
        db.session.add(job) # Add the new job info to the session.
        db.session.commit() # Commit the session to save all changes to the database.

        flash("✅ Job Info saved and new items added to dropdowns!", "success") # Flash success message.
        return redirect(url_for('admin.job_info_sheet')) # Redirect to the job info sheet.

    trades = [t.trade for t in WorkorderTemplate.query.with_entities(WorkorderTemplate.trade).distinct()]
    templates = WorkorderTemplate.query.all()
    categories = ['instrument', 'tool', 'device', 'equipment', 'operation']
    dropdown_items = {
        cat: [item.name for item in JobItem.query.filter_by(category=cat).distinct()]
        for cat in categories
    }

    return render_template("admin/job_info.html", trades=trades, templates=templates, dropdown_items=dropdown_items, edit_mode=False)


@admin_bp.route('/job-info-list', methods=['GET'])
@login_required
def job_info_list():
    # Get filters
    selected_trade = request.args.get('trade')
    selected_year = request.args.get('year')
    selected_aim = request.args.get('aim')

    # Base query
    query = JobInfo.query
    if selected_trade:
        query = query.filter_by(trade=selected_trade)
    if selected_year:
        query = query.filter_by(year=selected_year)
    if selected_aim:
        query = query.filter_by(aim=selected_aim)

    job_infos = query.options(db.joinedload(JobInfo.workorder)).all()

    trades = db.session.query(JobInfo.trade).distinct().all()
    aims = db.session.query(JobInfo.aim).distinct().all()
    years = ['Jr', 'Sr']

    return render_template("admin/job_info_list.html",
                           job_infos=job_infos,
                           trades=[t[0] for t in trades],
                           aims=[a[0] for a in aims],
                           years=years,
                           selected_trade=selected_trade,
                           selected_year=selected_year,
                           selected_aim=selected_aim)


@admin_bp.route('/job-info/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job_info(job_id):
    job = JobInfo.query.get_or_404(job_id)

    categories = ['instrument', 'tool', 'device', 'equipment', 'operation']
    dropdown_items = {
        cat: [item.name for item in JobItem.query.filter_by(category=cat).distinct()]
        for cat in categories
    }

    if request.method == 'POST':
        job.material = request.form.get('material')
        job.stock_size = request.form.get('stock_size')
        job.time = request.form.get('time')
        job.instruments = ','.join(request.form.getlist('instrument'))
        job.tools = ','.join(request.form.getlist('tool'))
        job.devices = ','.join(request.form.getlist('device'))
        job.equipment = ','.join(request.form.getlist('equipment'))
        job.operations = ','.join(request.form.getlist('operation'))
        job.other_items = request.form.get('other_items')

        db.session.commit()
        flash("✅ Job Info updated successfully!", "success")
        return redirect(url_for('admin.job_info_sheet'))
  
    return render_template("admin/job_info.html", job=job, dropdown_items=dropdown_items, edit_mode=True)


@admin_bp.route('/job-info/<int:job_id>/delete', methods=['POST', 'GET'])
@login_required
def delete_job_info(job_id):
    job = JobInfo.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash("Job Info deleted successfully ✅", "success")
    return redirect(url_for('admin.job_info_list'))

@admin_bp.route('/job-info/<int:job_id>/related-workorders')
@login_required
def related_workorder(job_id):
    job = JobInfo.query.get_or_404(job_id)

    related_workorders = WorkorderTemplate.query.filter_by(
        trade=job.trade,
        year=job.year,
        aim=job.aim
    ).all()

    return render_template('admin/related_workorders.html',
                           job=job,
                           workorders=related_workorders)