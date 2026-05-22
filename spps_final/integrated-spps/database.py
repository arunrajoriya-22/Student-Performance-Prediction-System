"""
database.py — NEW FILE (Integrated into Original Project)
SQLite database setup using Flask-SQLAlchemy.
Stores student records and prediction history.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize db — will be connected to app in app.py
db = SQLAlchemy()


# ══════════════════════════════════════════════
# TABLE 1: Student Records (CRUD)
# ══════════════════════════════════════════════
class Student(db.Model):
    """Stores student records added by admin."""
    __tablename__ = 'students'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    email       = db.Column(db.String(120), nullable=True)
    semester    = db.Column(db.Integer, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # One student → many predictions
    predictions = db.relationship('PredictionHistory', backref='student',
                                  lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Used for CSV export."""
        return {
            'id':          self.id,
            'name':        self.name,
            'roll_number': self.roll_number,
            'email':       self.email or '',
            'semester':    self.semester or '',
            'created_at':  self.created_at.strftime('%Y-%m-%d %H:%M')
        }


# ══════════════════════════════════════════════
# TABLE 2: Prediction History
# ══════════════════════════════════════════════
class PredictionHistory(db.Model):
    """Saves every prediction made through the system."""
    __tablename__ = 'prediction_history'

    id               = db.Column(db.Integer, primary_key=True)
    student_id       = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    student_name     = db.Column(db.String(100), nullable=True)

    # Input features
    study_hours      = db.Column(db.Float)
    attendance       = db.Column(db.Float)
    prev_sem_marks   = db.Column(db.Float)
    internal_marks   = db.Column(db.Float)
    assignment_pct   = db.Column(db.Float)
    participation    = db.Column(db.Integer)
    sleep_hours      = db.Column(db.Float)
    internet_hours   = db.Column(db.Float)

    # Outputs
    predicted_pct    = db.Column(db.Float)
    rf_predicted_pct = db.Column(db.Float, nullable=True)   # Random Forest result
    predicted_cat    = db.Column(db.String(20))
    confidence       = db.Column(db.Float, nullable=True)
    predicted_at     = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Used for CSV export."""
        return {
            'id':              self.id,
            'student_name':    self.student_name or 'Anonymous',
            'study_hours':     self.study_hours,
            'attendance':      self.attendance,
            'prev_sem_marks':  self.prev_sem_marks,
            'internal_marks':  self.internal_marks,
            'assignment_pct':  self.assignment_pct,
            'participation':   'Yes' if self.participation else 'No',
            'sleep_hours':     self.sleep_hours,
            'internet_hours':  self.internet_hours,
            'predicted_pct':   self.predicted_pct,
            'rf_predicted_pct': self.rf_predicted_pct or '',
            'predicted_cat':   self.predicted_cat,
            'confidence':      f"{self.confidence:.1f}%" if self.confidence else '',
            'predicted_at':    self.predicted_at.strftime('%Y-%m-%d %H:%M:%S')
        }


# ══════════════════════════════════════════════
# DATABASE HELPER: Dashboard Statistics
# ══════════════════════════════════════════════
def get_dashboard_stats():
    """Returns all stats needed for admin dashboard."""
    total_students    = Student.query.count()
    total_predictions = PredictionHistory.query.count()
    fail_count        = PredictionHistory.query.filter_by(predicted_cat='Fail').count()
    pass_count        = PredictionHistory.query.filter_by(predicted_cat='Pass').count()
    dist_count        = PredictionHistory.query.filter_by(predicted_cat='Distinction').count()

    all_pcts = PredictionHistory.query.with_entities(PredictionHistory.predicted_pct).all()
    avg_pct  = round(sum(p[0] for p in all_pcts) / len(all_pcts), 2) if all_pcts else 0

    recent = PredictionHistory.query.order_by(
                 PredictionHistory.predicted_at.desc()).limit(10).all()

    return {
        'total_students':    total_students,
        'total_predictions': total_predictions,
        'fail_count':        fail_count,
        'pass_count':        pass_count,
        'dist_count':        dist_count,
        'avg_pct':           avg_pct,
        'recent':            recent
    }
