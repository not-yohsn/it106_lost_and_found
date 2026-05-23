from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Optional, Length


class ClaimForm(FlaskForm):
    notes = TextAreaField(
        "Proof of ownership / notes (optional)",
        validators=[Optional(), Length(max=2000)],
        render_kw={
            "rows": 4,
            "placeholder": "Distinguishing details, contents, when/where you lost it…",
        },
    )
    submit = SubmitField("Submit claim")
