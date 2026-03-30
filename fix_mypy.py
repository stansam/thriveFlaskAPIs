import os
import re
import sys
from pathlib import Path

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content

    # 1. Base import
    content = re.sub(r'from \.base import (.*)', r'from app.models.base import \1', content)

    # 2. Type ignore on db.Model
    content = re.sub(r'(class \w+\(.*?db\.Model.*?\):)(?!\s*# type: ignore)', r'\1  # type: ignore[name-defined, misc]', content)

    # 3. db.DateTime -> DateTime, db.Date -> Date
    if 'db.DateTime' in content:
        content = content.replace('db.DateTime', 'DateTime')
        if 'DateTime' not in content.splitlines()[0:30]: # simplistic import check
            # Best effort import injection
            content = re.sub(r'(from sqlalchemy import \()', r'\1DateTime, ', content)
            if 'DateTime, ' not in content:
                 content = re.sub(r'(from sqlalchemy import .*?)\n', r'\1, DateTime\n', content, count=1)

    if 'db.Date' in content:
        content = content.replace('db.Date', 'Date')
        if 'Date' not in content.splitlines()[0:30]:
            content = re.sub(r'(from sqlalchemy import \()', r'\1Date, ', content)
            if 'Date, ' not in content:
                 content = re.sub(r'(from sqlalchemy import .*?)\n', r'\1, Date\n', content, count=1)

    if original != content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {filepath}")

def main():
    models_dir = Path("app/models")
    for f in models_dir.glob("*.py"):
        if f.name == "base.py":
            continue
        fix_file(f)

if __name__ == "__main__":
    main()
