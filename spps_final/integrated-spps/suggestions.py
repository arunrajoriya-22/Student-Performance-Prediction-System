"""
suggestions.py — NEW FILE (Integrated into Original Project)
Generates AI explanation for predictions and smart improvement suggestions.
Called from app.py after prediction is made.
"""


# ══════════════════════════════════════════════
# PREDICTION EXPLANATION SYSTEM
# ══════════════════════════════════════════════
def generate_explanation(features, predicted_pct, category):
    """
    Explains WHY a particular prediction was generated.
    Looks at each input feature and provides a human-readable reason.

    Args:
        features (dict): all 8 input feature values
        predicted_pct (float): predicted final percentage
        category (str): Fail / Pass / Distinction

    Returns:
        list of explanation strings
    """
    explanations = []
    f = features

    # Overall summary (shown first)
    if category == 'Distinction':
        explanations.append(
            "🏆 Overall: Strong academic inputs across multiple features — especially study hours, "
            "attendance, and marks — combined to produce a Distinction prediction."
        )
    elif category == 'Fail':
        explanations.append(
            "❌ Overall: Multiple critical factors like low attendance, insufficient study hours, "
            "or poor marks pulled the predicted score below the passing threshold."
        )
    else:
        explanations.append(
            "✅ Overall: Moderate performance across most inputs resulted in a Pass prediction. "
            "Improving key areas could push this toward Distinction."
        )

    # Study hours
    if f['study_hours'] >= 7:
        explanations.append(
            f"📚 Study Hours: {f['study_hours']}h/day is excellent — "
            "this strongly boosted your predicted score."
        )
    elif f['study_hours'] < 3:
        explanations.append(
            f"⚠️ Study Hours: Only {f['study_hours']}h/day — very low study time "
            "is a major reason for the lower predicted score."
        )
    else:
        explanations.append(
            f"📖 Study Hours: {f['study_hours']}h/day is moderate. "
            "Pushing to 7+ hours could significantly improve your result."
        )

    # Attendance
    if f['attendance'] >= 85:
        explanations.append(
            f"✅ Attendance: {f['attendance']}% is excellent — "
            "regular class attendance positively contributes to your score."
        )
    elif f['attendance'] < 60:
        explanations.append(
            f"🚫 Attendance: {f['attendance']}% is critically low — "
            "this is one of the biggest negative factors in your prediction."
        )
    elif f['attendance'] < 75:
        explanations.append(
            f"⚠️ Attendance: {f['attendance']}% is below the 75% minimum — "
            "this has negatively impacted the predicted percentage."
        )

    # Previous semester marks
    if f['prev_sem_marks'] >= 75:
        explanations.append(
            f"🎯 Previous Marks: {f['prev_sem_marks']}/100 shows consistent academic performance."
        )
    elif f['prev_sem_marks'] < 50:
        explanations.append(
            f"📉 Previous Marks: {f['prev_sem_marks']}/100 — historical academic struggles "
            "have reduced the current prediction."
        )

    # Internal marks
    if f['internal_marks'] >= 20:
        explanations.append(
            f"📝 Internal Marks: {f['internal_marks']}/25 — good internal scores "
            "have boosted your predicted final percentage."
        )
    elif f['internal_marks'] < 13:
        explanations.append(
            f"📝 Internal Marks: {f['internal_marks']}/25 is low — "
            "poor internal assessment performance has reduced the prediction."
        )

    # Assignment completion
    if f['assignment_pct'] >= 85:
        explanations.append(
            f"📋 Assignments: {f['assignment_pct']}% completion shows discipline and regularity."
        )
    elif f['assignment_pct'] < 50:
        explanations.append(
            f"❗ Assignments: Only {f['assignment_pct']}% completed — "
            "low submission rate reflects poor academic regularity."
        )

    # Internet usage
    if f['internet_hours'] >= 6:
        explanations.append(
            f"📱 Internet Usage: {f['internet_hours']}h/day is high — "
            "excessive non-academic internet use may be reducing study focus."
        )

    # Sleep
    if f['sleep_hours'] < 5:
        explanations.append(
            f"😴 Sleep: Only {f['sleep_hours']}h/day — insufficient sleep "
            "can negatively affect memory, focus, and exam performance."
        )
    elif f['sleep_hours'] >= 7:
        explanations.append(
            f"😴 Sleep: {f['sleep_hours']}h/day is healthy — "
            "adequate sleep supports better cognitive performance."
        )

    return explanations


# ══════════════════════════════════════════════
# SMART SUGGESTIONS SYSTEM
# ══════════════════════════════════════════════
def generate_suggestions(features, predicted_pct):
    """
    Generates personalized, actionable improvement suggestions.
    Priority levels: High, Medium, Low.

    Args:
        features (dict): all 8 input feature values
        predicted_pct (float): predicted final percentage

    Returns:
        list of suggestion dictionaries
    """
    suggestions = []
    f = features

    # ── HIGH PRIORITY ──
    if f['attendance'] < 75:
        gap = round(75 - f['attendance'], 1)
        suggestions.append({
            'priority': 'High',
            'icon': '📌',
            'title': 'Improve Attendance Urgently',
            'text': (
                f"Your attendance is {f['attendance']}%, which is {gap}% below the minimum 75% "
                f"requirement. Attend all remaining classes — even one extra class per week can "
                f"noticeably improve your predicted score."
            )
        })

    if f['study_hours'] < 4:
        suggestions.append({
            'priority': 'High',
            'icon': '📚',
            'title': 'Increase Daily Study Hours',
            'text': (
                f"You are studying only {f['study_hours']} hours per day. "
                f"Research shows 5–8 hours of focused study leads to significantly better performance. "
                f"Start by adding just 1 extra hour each day."
            )
        })

    if f['internal_marks'] < 15:
        suggestions.append({
            'priority': 'High',
            'icon': '📝',
            'title': 'Focus on Internal Assessments',
            'text': (
                f"Internal marks of {f['internal_marks']}/25 are below expected. "
                f"Prepare thoroughly for unit tests, practicals, and lab work — "
                f"these directly boost your overall marks."
            )
        })

    # ── MEDIUM PRIORITY ──
    if f['assignment_pct'] < 70:
        suggestions.append({
            'priority': 'Medium',
            'icon': '✅',
            'title': 'Complete Pending Assignments',
            'text': (
                f"Assignment completion is only {f['assignment_pct']}%. "
                f"Submit all pending work — even late submissions are better than none. "
                f"Set a daily target to clear the backlog."
            )
        })

    if f['internet_hours'] > 5:
        suggestions.append({
            'priority': 'Medium',
            'icon': '📱',
            'title': 'Reduce Non-Academic Internet Usage',
            'text': (
                f"You are spending {f['internet_hours']} hours/day on the internet. "
                f"Limit recreational usage to 2–3 hours and redirect the saved time to study."
            )
        })

    if f['prev_sem_marks'] < 55:
        suggestions.append({
            'priority': 'Medium',
            'icon': '🎯',
            'title': 'Review Previous Semester Topics',
            'text': (
                f"Previous semester marks of {f['prev_sem_marks']}/100 suggest foundational gaps. "
                f"Spend 30 minutes daily revisiting past subjects — strong basics improve current performance."
            )
        })

    # ── LOW PRIORITY ──
    if f['sleep_hours'] < 6:
        suggestions.append({
            'priority': 'Low',
            'icon': '😴',
            'title': 'Improve Your Sleep Schedule',
            'text': (
                f"Only {f['sleep_hours']} hours of sleep impairs memory and concentration. "
                f"Aim for 7–8 hours daily, especially before exams and internal assessments."
            )
        })

    if not f['participation']:
        suggestions.append({
            'priority': 'Low',
            'icon': '🏅',
            'title': 'Participate in Activities',
            'text': (
                "Extracurricular participation builds soft skills, improves focus, and reduces exam stress. "
                "Join at least one club or academic event this semester."
            )
        })

    # If everything looks good
    if predicted_pct >= 80 and not suggestions:
        suggestions.append({
            'priority': 'Info',
            'icon': '🌟',
            'title': 'Excellent — Keep It Up!',
            'text': (
                "Your inputs look strong across all areas! Maintain your current study discipline "
                "and attendance above 85%, and you are well on track for a top result."
            )
        })

    return suggestions
