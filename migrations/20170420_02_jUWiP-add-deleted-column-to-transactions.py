"""
Add deleted column to transactions
"""

from yoyo import step

__depends__ = {'20170420_01_WYWkH-add-deleted-column-to-accounts'}

steps = [
    step("ALTER TABLE transactions ADD COLUMN deleted BOOLEAN NOT NULL DEFAULT 0")
]
