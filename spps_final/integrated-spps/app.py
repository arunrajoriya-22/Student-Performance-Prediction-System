"""
app.py — Student Performance Prediction System (UPGRADED)
ORIGINAL project base kept intact. New features added cleanly on top.
"""
import os, csv, io, json, pickle
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, Response, jsonify)
from database   import db, Student, PredictionHistory, get_dashboard_stats
from suggestions import generate_explanation, generate_suggestions

app = Flask(__name__)
app.secret_key = 'spps_secret_key_2024'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# NEW: database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR,'instance','spps.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os.makedirs(os.path.join(BASE_DIR,'instance'), exist_ok=True)
db.init_app(app)
with app.app_context():
    db.create_all()
    print("✅ Database ready.")

# ORIGINAL: load base models
with open(os.path.join(BASE_DIR,'regression_model.pkl'),'rb') as f: reg_model = pickle.load(f)
with open(os.path.join(BASE_DIR,'classification_model.pkl'),'rb') as f: clf_model = pickle.load(f)
with open(os.path.join(BASE_DIR,'scaler.pkl'),'rb') as f: scaler = pickle.load(f)
with open(os.path.join(BASE_DIR,'metrics.json'),'r') as f: metrics = json.load(f)

# NEW: optional Random Forest models
rf_reg_model = rf_clf_model = rf_scaler = None
if os.path.exists(os.path.join(BASE_DIR,'rf_regressor.pkl')):
    with open(os.path.join(BASE_DIR,'rf_regressor.pkl'),'rb') as f: rf_reg_model = pickle.load(f)
    with open(os.path.join(BASE_DIR,'rf_classifier.pkl'),'rb') as f: rf_clf_model = pickle.load(f)
    with open(os.path.join(BASE_DIR,'rf_scaler.pkl'),'rb') as f:     rf_scaler    = pickle.load(f)
    print("✅ Random Forest models loaded.")
else:
    print("ℹ️  RF models not found. Run: python train_rf.py to enable multi-model.")

FEATURE_ORDER = ['study_hours','attendance','prev_sem_marks','internal_marks',
                 'assignment_pct','participation','sleep_hours','internet_hours']
CLASS_LABELS  = {0:'Fail',1:'Pass',2:'Distinction'}
CLASS_COLORS  = {0:'#ef4444',1:'#3b82f6',2:'#10b981'}
CLASS_ICONS   = {0:'❌',1:'✅',2:'🏆'}
ADMIN_USERNAME = 'BTAM24O1017'
ADMIN_PASSWORD = 'Arun@1234'

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel.','warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ─── ORIGINAL ROUTES ──────────────────────────────────────────
@app.route('/')
def index(): return render_template('index.html')

@app.route('/predict', methods=['GET'])
def predict():
    students = Student.query.order_by(Student.name).all()
    return render_template('predict.html', students=students)

@app.route('/predict', methods=['POST'])
def predict_post():
    try:
        features = []
        for feat in FEATURE_ORDER:
            val = request.form.get(feat)
            if val is None or val.strip() == '': raise ValueError(f"Missing field: {feat}")
            features.append(float(val))
        sh,at,ps,im,ap,pa,slp,ih = features
        errors=[]
        if not(0<=sh<=16):   errors.append("Study hours must be 0–16.")
        if not(0<=at<=100):  errors.append("Attendance must be 0–100.")
        if not(0<=ps<=100):  errors.append("Prev marks must be 0–100.")
        if not(0<=im<=25):   errors.append("Internal marks must be 0–25.")
        if not(0<=ap<=100):  errors.append("Assignment % must be 0–100.")
        if pa not in [0,1]:  errors.append("Participation must be 0 or 1.")
        if not(0<=slp<=16):  errors.append("Sleep hours must be 0–16.")
        if not(0<=ih<=16):   errors.append("Internet hours must be 0–16.")
        if errors: return render_template('predict.html',errors=errors,form_data=request.form)

        import pandas as pd
        X = pd.DataFrame([features], columns=FEATURE_ORDER)
        X_scaled = scaler.transform(X)
        predicted_pct = round(max(0,min(100,float(reg_model.predict(X_scaled)[0]))),2)
        pred_class = int(clf_model.predict(X_scaled)[0])
        proba      = clf_model.predict_proba(X_scaled)[0]
        confidence = round(float(max(proba))*100,2)
        pred_class = 2 if predicted_pct>=75 else (1 if predicted_pct>=40 else 0)
        category   = CLASS_LABELS[pred_class]
        color      = CLASS_COLORS[pred_class]
        icon       = CLASS_ICONS[pred_class]
        class_probs = {CLASS_LABELS[i]:round(float(proba[i])*100,2) for i in range(len(proba))}
        input_summary = {
            'Study Hours / Day':f"{sh} hrs",'Attendance':f"{at}%",
            'Previous Sem Marks':f"{ps} / 100",'Internal Marks':f"{im} / 25",
            'Assignment Completion':f"{ap}%",
            'Activity Participation':'Yes' if pa==1 else 'No',
            'Sleep Hours / Day':f"{slp} hrs",'Internet Usage / Day':f"{ih} hrs"
        }
        # NEW: Random Forest
        rf_pct = None
        if rf_reg_model and rf_scaler:
            X_rf  = rf_scaler.transform(X)
            rf_pct = round(max(0,min(100,float(rf_reg_model.predict(X_rf)[0]))),2)
        # NEW: explanation + suggestions
        features_dict = {'study_hours':sh,'attendance':at,'prev_sem_marks':ps,
                         'internal_marks':im,'assignment_pct':ap,'participation':pa,
                         'sleep_hours':slp,'internet_hours':ih}
        explanation = generate_explanation(features_dict, predicted_pct, category)
        suggestions = generate_suggestions(features_dict, predicted_pct)
        # NEW: grade letter
        grade = ('O' if predicted_pct>=90 else 'A+' if predicted_pct>=80 else 'A' if predicted_pct>=70
                 else 'B+' if predicted_pct>=60 else 'B' if predicted_pct>=50 else 'C' if predicted_pct>=40 else 'F')
        student_name = request.form.get('student_name','').strip() or 'Anonymous'
        student_id   = request.form.get('student_id') or None
        # NEW: save to DB
        hist = PredictionHistory(
            student_id=int(student_id) if student_id else None, student_name=student_name,
            study_hours=sh, attendance=at, prev_sem_marks=ps, internal_marks=im,
            assignment_pct=ap, participation=int(pa), sleep_hours=slp, internet_hours=ih,
            predicted_pct=predicted_pct, rf_predicted_pct=rf_pct,
            predicted_cat=category, confidence=confidence)
        db.session.add(hist); db.session.commit()
        return render_template('result.html',
            predicted_pct=predicted_pct,category=category,color=color,icon=icon,
            confidence=confidence,class_probs=class_probs,input_summary=input_summary,
            rf_pct=rf_pct,grade=grade,student_name=student_name,
            explanation=explanation,suggestions=suggestions)
    except ValueError as ve:
        return render_template('predict.html',errors=[str(ve)],form_data=request.form)
    except Exception as e:
        return render_template('predict.html',errors=[f"Error: {str(e)}"],form_data=request.form)

@app.route('/about')
def about(): return render_template('about.html',metrics=metrics)

@app.route('/contact')
def contact(): return render_template('contact.html')

# ─── NEW ADMIN ROUTES ─────────────────────────────────────────
@app.route('/admin-login',methods=['GET','POST'])
def admin_login():
    if session.get('admin_logged_in'): return redirect(url_for('admin_dashboard'))
    if request.method=='POST':
        if request.form.get('username')==ADMIN_USERNAME and request.form.get('password')==ADMIN_PASSWORD:
            session['admin_logged_in']=True; flash('Welcome, Admin! 👋','success')
            return redirect(url_for('admin_dashboard'))
        flash('Incorrect credentials.','danger')
    return render_template('admin_login.html')

@app.route('/admin-logout')
def admin_logout():
    session.clear(); flash('Logged out.','info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html',stats=get_dashboard_stats())

@app.route('/admin/students')
@login_required
def admin_students():
    return render_template('admin_students.html',students=Student.query.order_by(Student.created_at.desc()).all())

@app.route('/admin/students/add',methods=['POST'])
@login_required
def add_student():
    name=request.form.get('name','').strip(); roll=request.form.get('roll_number','').strip()
    if not name or not roll: flash('Name and Roll No. required.','danger'); return redirect(url_for('admin_students'))
    if Student.query.filter_by(roll_number=roll).first(): flash(f'{roll} already exists.','warning'); return redirect(url_for('admin_students'))
    sem=request.form.get('semester','').strip()
    db.session.add(Student(name=name,roll_number=roll,email=request.form.get('email','').strip() or None,semester=int(sem) if sem.isdigit() else None))
    db.session.commit(); flash(f'Student {name} added! ✅','success')
    return redirect(url_for('admin_students'))

@app.route('/admin/students/delete/<int:sid>',methods=['POST'])
@login_required
def delete_student(sid):
    st=Student.query.get_or_404(sid); n=st.name; db.session.delete(st); db.session.commit()
    flash(f'{n} deleted.','info'); return redirect(url_for('admin_students'))

@app.route('/admin/students/view/<int:sid>')
@login_required
def view_student(sid):
    st=Student.query.get_or_404(sid)
    hist=PredictionHistory.query.filter_by(student_id=sid).order_by(PredictionHistory.predicted_at.desc()).all()
    return render_template('admin_student_profile.html',student=st,history=hist)

@app.route('/admin/history')
@login_required
def admin_history():
    page=request.args.get('page',1,type=int); cat=request.args.get('category','')
    q=PredictionHistory.query.order_by(PredictionHistory.predicted_at.desc())
    if cat: q=q.filter_by(predicted_cat=cat)
    return render_template('admin_history.html',history=q.paginate(page=page,per_page=15,error_out=False),category=cat)

@app.route('/admin/history/delete/<int:pid>',methods=['POST'])
@login_required
def delete_prediction(pid):
    p=PredictionHistory.query.get_or_404(pid); db.session.delete(p); db.session.commit()
    flash('Record deleted.','info'); return redirect(url_for('admin_history'))

@app.route('/admin/model-performance')
@login_required
def model_performance():
    return render_template('admin_model_performance.html',metrics=metrics)

@app.route('/admin/export/predictions/csv')
@login_required
def export_predictions_csv():
    preds=PredictionHistory.query.order_by(PredictionHistory.predicted_at.desc()).all()
    if not preds: flash('No data to export.','warning'); return redirect(url_for('admin_history'))
    out=io.StringIO(); w=csv.DictWriter(out,fieldnames=list(preds[0].to_dict().keys()))
    w.writeheader(); [w.writerow(p.to_dict()) for p in preds]; out.seek(0)
    return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':f'attachment; filename=predictions_{datetime.now().strftime("%Y%m%d")}.csv'})

@app.route('/admin/export/students/csv')
@login_required
def export_students_csv():
    sts=Student.query.order_by(Student.name).all()
    if not sts: flash('No students to export.','warning'); return redirect(url_for('admin_students'))
    out=io.StringIO(); w=csv.DictWriter(out,fieldnames=list(sts[0].to_dict().keys()))
    w.writeheader(); [w.writerow(s.to_dict()) for s in sts]; out.seek(0)
    return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':f'attachment; filename=students_{datetime.now().strftime("%Y%m%d")}.csv'})

@app.route('/admin/export/predictions/json')
@login_required
def export_predictions_json():
    preds=PredictionHistory.query.order_by(PredictionHistory.predicted_at.desc()).all()
    return Response(json.dumps([p.to_dict() for p in preds],indent=2),mimetype='application/json',
                    headers={'Content-Disposition':f'attachment; filename=predictions_{datetime.now().strftime("%Y%m%d")}.json'})

@app.route('/api/category-chart')
@login_required
def category_chart_data():
    return jsonify({'labels':['Fail','Pass','Distinction'],
        'values':[PredictionHistory.query.filter_by(predicted_cat=c).count() for c in ['Fail','Pass','Distinction']],
        'colors':['#ef4444','#3b82f6','#10b981']})

@app.route('/api/prediction-trend')
@login_required
def prediction_trend():
    preds=list(reversed(PredictionHistory.query.order_by(PredictionHistory.predicted_at.desc()).limit(30).all()))
    return jsonify({'labels':[p.predicted_at.strftime('%d/%m') for p in preds],'values':[p.predicted_pct for p in preds]})

@app.errorhandler(404)
def page_not_found(e): return render_template('404.html'),404
@app.errorhandler(500)
def internal_error(e): return render_template('404.html',message="Internal server error."),500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
