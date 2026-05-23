"""Marshmallow schemas for /api/v2.

Each schema declares the JSON shape used both for response serialization
(replacing v1's hand-rolled to_dict() calls) and for incoming-request
validation. Flask-Smorest picks up these schemas via @blp.arguments and
@blp.response decorators and auto-generates the OpenAPI spec.
"""
from marshmallow import Schema, fields, validate


class LoginRequestSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class UserSchema(Schema):
    user_id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    email = fields.Email(required=True)
    phone = fields.String(allow_none=True)
    role = fields.String(
        validate=validate.OneOf(["student", "staff", "admin"]),
        dump_default="student",
    )
    created_at = fields.DateTime(dump_only=True)


class TokenResponseSchema(Schema):
    token = fields.String(required=True)
    user = fields.Nested(UserSchema, required=True)


class LostReportSchema(Schema):
    report_id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    item_name = fields.String(required=True)
    description = fields.String(allow_none=True)
    category = fields.String(allow_none=True)
    location = fields.String(allow_none=True)
    date_lost = fields.Date(allow_none=True)
    photo_path = fields.String(allow_none=True, dump_only=True)
    status = fields.String(
        validate=validate.OneOf(["reported", "matched", "claimed", "closed"]),
        dump_default="reported",
    )
    created_at = fields.DateTime(dump_only=True)


class LostReportCreateSchema(Schema):
    item_name = fields.String(required=True)
    description = fields.String(allow_none=True)
    category = fields.String(allow_none=True)
    location = fields.String(allow_none=True)
    date_lost = fields.Date(allow_none=True)


class LostReportUpdateSchema(Schema):
    """All-optional variant of LostReportCreate for PUT bodies."""
    item_name = fields.String()
    description = fields.String(allow_none=True)
    category = fields.String(allow_none=True)
    location = fields.String(allow_none=True)
    date_lost = fields.Date(allow_none=True)


class FoundItemSchema(Schema):
    item_id = fields.Integer(dump_only=True)
    finder_id = fields.Integer(allow_none=True)
    logged_by = fields.Integer(allow_none=True, dump_only=True)
    item_name = fields.String(required=True)
    description = fields.String(allow_none=True)
    category = fields.String(allow_none=True)
    location_found = fields.String(allow_none=True)
    date_found = fields.Date(allow_none=True)
    photo_path = fields.String(allow_none=True, dump_only=True)
    status = fields.String(
        validate=validate.OneOf(["logged", "matched", "released"]),
        dump_default="logged",
    )
    created_at = fields.DateTime(dump_only=True)


class ClaimSchema(Schema):
    claim_id = fields.Integer(dump_only=True)
    match_id = fields.Integer(required=True)
    claimant_id = fields.Integer(dump_only=True)
    verified_by = fields.Integer(allow_none=True, dump_only=True)
    status = fields.String(
        validate=validate.OneOf(["pending", "approved", "rejected", "released"]),
        dump_default="pending",
    )
    notes = fields.String(allow_none=True)
    submitted_at = fields.DateTime(dump_only=True)
    resolved_at = fields.DateTime(allow_none=True, dump_only=True)


class ClaimCreateSchema(Schema):
    match_id = fields.Integer(required=True)
    notes = fields.String(allow_none=True)


class PaginationQuerySchema(Schema):
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Integer(
        load_default=20, validate=validate.Range(min=1, max=100)
    )


def paginated(item_schema):
    """Build a paginated wrapper schema for any item schema."""
    class PaginatedSchema(Schema):
        data = fields.List(fields.Nested(item_schema))
        page = fields.Integer()
        per_page = fields.Integer()
        total = fields.Integer()
    PaginatedSchema.__name__ = f"Paginated{item_schema.__name__}"
    return PaginatedSchema
