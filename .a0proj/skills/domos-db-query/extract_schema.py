#!/usr/bin/env python3
"""Extract database schema from SQLAlchemy models.

Usage:
    python extract_schema.py

This script reads all model files and outputs a structured schema description.
Useful for keeping documentation in sync with actual code.
"""

import os
import re
import sys
from pathlib import Path

# Path to models directory
MODELS_DIR = Path("/a0/usr/projects/domos/mvp1-cashier/backend/app/models")

def extract_table_info(file_path: Path) -> dict:
    """Extract table information from a model file."""
    content = file_path.read_text(encoding='utf-8')
    
    result = {
        'file': file_path.name,
        'tables': []
    }
    
    # Find class definitions that inherit from Base
    class_pattern = r'class\s+(\w+)\(.*Base.*\):'
    classes = re.findall(class_pattern, content)
    
    for class_name in classes:
        table_info = {
            'class_name': class_name,
            'table_name': None,
            'columns': []
        }
        
        # Find __tablename__
        tablename_pattern = rf'class\s+{class_name}.*?__tablename__\s*=\s*["\']([\w_]+)["\']'
        tablename_match = re.search(tablename_pattern, content, re.DOTALL)
        if tablename_match:
            table_info['table_name'] = tablename_match.group(1)
        
        # Find column definitions using Mapped pattern
        # Pattern: column_name: Mapped[type] = mapped_column(...)
        column_pattern = r'(\w+):\s*Mapped\[([^\]]+)\]\s*=\s*mapped_column\(([^)]+(?:\([^)]*\)[^)]*)*)\)'
        
        for match in re.finditer(column_pattern, content):
            col_name = match.group(1)
            col_type = match.group(2).strip()
            col_args = match.group(3)
            
            # Determine if nullable
            nullable = '| None' in col_type or 'None |' in col_type or 'Optional' in col_type
            if 'nullable=True' in col_args:
                nullable = True
            elif 'nullable=False' in col_args:
                nullable = False
            
            # Check if primary key
            is_pk = 'primary_key=True' in col_args
            
            # Check for foreign key
            fk_match = re.search(r'ForeignKey\(["\']([\w_.]+)["\']', col_args)
            fk = fk_match.group(1) if fk_match else None
            
            # Extract comment if present
            comment_match = re.search(r'comment=["\']([^"\']+)["\']', col_args)
            comment = comment_match.group(1) if comment_match else None
            
            table_info['columns'].append({
                'name': col_name,
                'type': col_type,
                'nullable': nullable,
                'primary_key': is_pk,
                'foreign_key': fk,
                'comment': comment
            })
        
        # Also check for Column() style (older pattern)
        old_column_pattern = r'(\w+)\s*=\s*Column\(([^)]+(?:\([^)]*\)[^)]*)*)\)'
        for match in re.finditer(old_column_pattern, content):
            col_name = match.group(1)
            col_args = match.group(2)
            
            # Skip if already found via Mapped pattern
            if any(c['name'] == col_name for c in table_info['columns']):
                continue
            
            # Try to extract type
            type_match = re.match(r'(\w+)', col_args)
            col_type = type_match.group(1) if type_match else 'unknown'
            
            nullable = 'nullable=True' in col_args or 'nullable=False' not in col_args
            is_pk = 'primary_key=True' in col_args
            
            table_info['columns'].append({
                'name': col_name,
                'type': col_type,
                'nullable': nullable,
                'primary_key': is_pk,
                'foreign_key': None,
                'comment': None
            })
        
        if table_info['table_name']:
            result['tables'].append(table_info)
    
    return result

def print_schema_markdown(all_tables: list):
    """Print schema in Markdown format."""
    print("# Database Schema (auto-generated)\n")
    print(f"Generated from: `{MODELS_DIR}`\n")
    
    for table in all_tables:
        print(f"## Table: `{table['table_name']}` (class: {table['class_name']})\n")
        print("| Column | Type | Nullable | PK | FK | Description |")
        print("|--------|------|----------|----|----|-------------|")
        
        for col in table['columns']:
            nullable = "YES" if col['nullable'] else "NO"
            pk = "✓" if col['primary_key'] else ""
            fk = col['foreign_key'] or ""
            comment = col['comment'] or ""
            print(f"| {col['name']} | {col['type']} | {nullable} | {pk} | {fk} | {comment} |")
        
        print()

def main():
    if not MODELS_DIR.exists():
        print(f"Error: Models directory not found: {MODELS_DIR}", file=sys.stderr)
        sys.exit(1)
    
    all_tables = []
    
    for model_file in sorted(MODELS_DIR.glob("*.py")):
        if model_file.name == "__init__.py":
            continue
        
        info = extract_table_info(model_file)
        all_tables.extend(info['tables'])
    
    print_schema_markdown(all_tables)
    
    # Print warnings for common issues
    print("\n## ⚠️ Common Mistakes to Avoid\n")
    
    # Check for tables without 'status' column that might be confused
    tables_without_status = []
    tables_with_status = []
    
    for table in all_tables:
        has_status = any(col['name'] == 'status' for col in table['columns'])
        if has_status:
            tables_with_status.append(table['table_name'])
        else:
            tables_without_status.append(table['table_name'])
    
    if tables_with_status and tables_without_status:
        print(f"Tables WITH `status` column: {', '.join(tables_with_status)}")
        print(f"Tables WITHOUT `status` column: {', '.join(tables_without_status)}")
        print("\n**Do not use `status` on tables that don't have it!**")

if __name__ == "__main__":
    main()
