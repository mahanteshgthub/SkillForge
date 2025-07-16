import os
from flask import Blueprint, render_template, redirect, flash, url_for, request, current_app
from werkzeug.utils import secure_filename
from .forms import WorkorderForm
from .models import db, WorkorderTemplate, DimensionalFeature, SubjectiveFeature
from flask_login import login_required, current_user

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/workorders/new", methods=["GET", "POST"])
@login_required
def create_workorder():
    if not current_user.is_admin():
        flash("Access denied", "danger")
        return redirect(url_for("dashboard"))

    form = WorkorderForm()
    dim_labels = list("ABCDEFGHIJ")
    subj_labels = list("KLMNO")

    if form.validate_on_submit():
        total_marks = sum(f.marks.data for f in form.dim_features) + \
                      sum(f.marks.data for f in form.subj_features) + 20  # fixed attitude marks

        if total_marks > 100:
            flash(f"Total marks ({total_marks}) exceed 100. Please adjust.", "danger")
            return render_template("admin/workorder_form.html", form=form,
                                   dim_labels=dim_labels, subj_labels=subj_labels)

        filename = None
        if form.job_image.data:
            filename = secure_filename(form.job_image.data.filename)
            path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
            form.job_image.data.save(path)

        work = WorkorderTemplate(
            trade=form.trade.data,
            year=form.year.data,
            exercise_no=form.exercise_no.data,
            aim=form.aim.data,
            job_image=filename,
            common_tolerance=form.common_tolerance.data
        )
        db.session.add(work)
        db.session.flush()

        for i, f in enumerate(form.dim_features):
            dim = DimensionalFeature(
                label=dim_labels[i],
                size=f.size.data,
                marks=f.marks.data,
                workorder_id=work.id
            )
            db.session.add(dim)

        for i, f in enumerate(form.subj_features):
            subj = SubjectiveFeature(
                label=subj_labels[i],
                operation=f.operation.data,
                marks=f.marks.data,
                workorder_id=work.id
            )
            db.session.add(subj)

        db.session.commit()
        flash("Workorder template created successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("admin/workorder_form.html", form=form,dim_labels=dim_labels, subj_labels=subj_labels)