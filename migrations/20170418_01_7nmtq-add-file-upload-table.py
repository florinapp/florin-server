"""
Add file upload table
"""

from yoyo import step

__depends__ = {'20170416_02_OcHWl-add-stock-categories'}

steps = [
    step("""
CREATE TABLE file_uploads (
            id INTEGER NOT NULL,
            filename VARCHAR(255) NOT NULL,
            uploaded_at DATETIME NOT NULL,
            file_content TEXT NOT NULL,
            account_id INTEGER,
            account_signature VARCHAR(128),
            PRIMARY KEY (id),
            FOREIGN KEY(account_id) REFERENCES accounts (id)
         );"""
         )
]
