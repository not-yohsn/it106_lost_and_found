from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

CATEGORIES = [
    ("electronics", "Electronics"),
    ("ids_cards", "ID / Cards"),
    ("bags_wallets", "Bags & Wallets"),
    ("clothing", "Clothing"),
    ("books_notes", "Books & Notes"),
    ("keys", "Keys"),
    ("jewelry", "Jewelry"),
    ("other", "Other"),
]

IMAGE_EXTS = ["jpg", "jpeg", "png", "gif", "webp"]


class LostReportForm(FlaskForm):
    item_name = StringField(
        "Item name", validators=[DataRequired(), Length(max=120)]
    )
    description = TextAreaField("Description", validators=[Optional()])
    category = SelectField("Category", choices=CATEGORIES, default="other")
    location = StringField(
        "Where did you lose it?", validators=[Optional(), Length(max=120)]
    )
    date_lost = DateField("Date lost", validators=[Optional()])
    photo = FileField(
        "Photo (optional)",
        validators=[FileAllowed(IMAGE_EXTS, "Images only (jpg, png, gif, webp).")],
    )
    submit = SubmitField("Submit report")
