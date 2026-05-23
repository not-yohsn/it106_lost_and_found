"""GET /api/v2/found-items — read-only summary endpoint for v2."""
from flask_smorest import Blueprint, abort

from ...extensions import db
from ...models import FoundItem
from .auth_helpers import api_login_required
from .schemas import FoundItemSchema, PaginationQuerySchema, paginated

blp = Blueprint(
    "found_items_v2", __name__,
    url_prefix="/api/v2/found-items",
    description="Items logged at the lost-and-found desk.",
)


@blp.route("", methods=["GET"])
@blp.arguments(PaginationQuerySchema, location="query")
@blp.response(200, paginated(FoundItemSchema))
@api_login_required
def list_found_items(args):
    """List found items — paginated."""
    pagination = (
        FoundItem.query
        .order_by(FoundItem.created_at.desc())
        .paginate(page=args["page"], per_page=args["per_page"], error_out=False)
    )
    return {
        "data": pagination.items,
        "page": args["page"],
        "per_page": args["per_page"],
        "total": pagination.total,
    }


@blp.route("/<int:item_id>", methods=["GET"])
@blp.response(200, FoundItemSchema)
@blp.alt_response(404, description="Item not found.")
@api_login_required
def get_found_item(item_id):
    """Fetch a single found item."""
    item = db.session.get(FoundItem, item_id)
    if item is None:
        abort(404, message="not_found")
    return item
