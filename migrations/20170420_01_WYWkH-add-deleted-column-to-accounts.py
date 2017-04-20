"""
add deleted column to accounts
"""

from yoyo import step

__depends__ = {'20170418_01_7nmtq-add-file-upload-table'}

steps = [
    step("ALTER TABLE accounts ADD COLUMN deleted BOOLEAN NOT NULL DEFAULT FALSE")
]
