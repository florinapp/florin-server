"""
Add account_types
"""

from yoyo import step

__depends__ = {'20170423_02_Eryn4-add-stock-categories'}

steps = [
    step("""\
CREATE TABLE account_types (
    name VARCHAR NOT NULL,
    PRIMARY KEY (name)
);"""),
    step("""INSERT INTO account_types VALUES ("chequing")"""),
    step("""INSERT INTO account_types VALUES ("savings")"""),
    step("""INSERT INTO account_types VALUES ("credit")"""),
    step("""INSERT INTO account_types VALUES ("investment")"""),
]
