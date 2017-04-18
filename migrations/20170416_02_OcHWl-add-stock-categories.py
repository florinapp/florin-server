"""
add stock categories
"""

from yoyo import step

__depends__ = {'20170416_01_ZLKvX-bootstrap'}

categories = {
    (1, 'Automobile', 'expense'): [
        'Car Insurance',
        'Car Payment',
        'Gasoline',
        'Highway tolls',
        'Maintenance',
    ],
    (2, 'Bank Charges', 'expense'): [
        'Interest paid',
        'Service charge',
    ],
    (3, 'Bills', 'expense'): [
        'Cable/Satellite Television',
        'Cell Phone',
        'Hydro',
        'Natural Gas/Oil',
        'Online/Internet Service',
        'Telephone',
    ],
    (4, 'Charitable Donations', 'expense'): [
        'Charity',
        'Church',
    ],
    (5, 'Shopping', 'expense'): [
        'Clothing',
        'Groceries',
        'Electronics',
        'Entertainment',
        'Hobbies',
        'Other',
    ],
    (6, 'Dining Out', 'expense'): [
        'Fast Food/Coffee Shops',
        'Restaurants',
    ],
    (7, 'Fees', 'expense'): [],
    (8, 'Gifts', 'expense'): [],
    (9, 'Health', 'expense'): [
        'Health Care',
        'Personal Care',
    ],
    (10, 'Home Improvement', 'expense'): [],
    (11, 'Mortgage', 'expense'): [],
    (12, 'Pet Care', 'expense'): [],
    (13, 'Public Transportation', 'expense'): [],
    (14, 'Travel/Vacation', 'expense'): [
        'Lodging',
        'Travel',
    ],
    (50, 'Interest', 'income'): [],
    (51, 'Rewards', 'income'): [],
    (52, 'Salary', 'income'): [],
    (53, 'Salary (Spouse)', 'income'): [],
    (54, 'Tax Returns', 'income'): [],
    (65534, 'Internal Transfer', 'other'): [],
    (65535, 'TBD', 'other'): [],
}


steps = []


for (id, name, type), child_categories in categories.items():
    steps.append(step('INSERT INTO categories VALUES ({id}, "{name}", NULL, "{type}")'.format(
        id=id, name=name, type=type)))
    for idx, child_category_name in enumerate(child_categories):
        child_id = id * 1000 + idx
        steps.append(step('INSERT INTO categories VALUES ({id}, "{name}", {parent_id}, "{type}")'.format(
            id=child_id, name=child_category_name, parent_id=id, type=type)))
