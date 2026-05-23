from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

from ..reports.forms import CATEGORIES, IMAGE_EXTS


class FoundItemForm(FlaskForm):
    item_name = StringField(
        "Item name", validators=[DataRequired(), Length(max=120)]
    )
    description = TextAreaField("Description", validators=[Optional()])
    category = SelectField("Category", choices=CATEGORIES, default="other")
    location_found = StringField(
        "Where did you find it?", validators=[Optional(), Length(max=120)]
    )
    date_found = DateField("Date found", validators=[Optional()])
    photo = FileField(
        "Photo (optional)",
        validators=[FileAllowed(IMAGE_EXTS, "Images only (jpg, png, gif, webp).")],
    )
    submit = SubmitField("Log item")
