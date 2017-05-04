from florin.db import Category
from florin.constants import TBD_CATEGORY_ID, INTERNAL_TRANSFER_CATEGORY_ID, INCOME_PARENT_CATEGORY_ID  # noqa


def get(app):
    categories = app.session.query(Category).all()

    flat_categories = [category.to_dict() for category in categories]
    top_level_categories = [c for c in flat_categories if c['parent_id'] is None]
    for category in top_level_categories:
        category['subcategories'] = [c for c in flat_categories if c['parent_id'] == category['id']]
    return {
        'categories': top_level_categories
    }
