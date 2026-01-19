#!/usr/bin/env python3
"""
Asset Viewer Web Application
Displays assets from SQL dump in a searchable grid with detail view
"""

from flask import Flask, render_template, jsonify
import re
from collections import defaultdict
import os

app = Flask(__name__)

# Global data storage
DATA = {
    'assets': {},
    'asset_categories': {},
    'brands': {},
    'models': {},
    'asset_category_fields': {},
    'asset_field_values': defaultdict(dict),
    'customers': {},
    'engineers': {},
    'asset_updates': defaultdict(list),
    'loaded': False
}

SQL_FILE = "/Users/davidhamilton/Dev/Ai Apoyar Source Data /apoyar_db.sql"


def parse_insert_values(line):
    """Parse VALUES from an INSERT statement."""
    match = re.search(r'VALUES\s*(.+);?\s*$', line, re.IGNORECASE)
    if not match:
        return []

    values_str = match.group(1)
    records = []
    current_record = []
    current_value = ""
    in_string = False
    escape_next = False
    paren_depth = 0

    i = 0
    while i < len(values_str):
        char = values_str[i]

        if escape_next:
            current_value += char
            escape_next = False
            i += 1
            continue

        if char == '\\':
            escape_next = True
            current_value += char
            i += 1
            continue

        if char == "'" and not in_string:
            in_string = True
            i += 1
            continue
        elif char == "'" and in_string:
            if i + 1 < len(values_str) and values_str[i + 1] == "'":
                current_value += "'"
                i += 2
                continue
            in_string = False
            i += 1
            continue

        if in_string:
            current_value += char
            i += 1
            continue

        if char == '(':
            if paren_depth == 0:
                current_record = []
                current_value = ""
            paren_depth += 1
            i += 1
            continue
        elif char == ')':
            paren_depth -= 1
            if paren_depth == 0:
                current_record.append(current_value.strip())
                records.append(current_record)
                current_value = ""
            i += 1
            continue
        elif char == ',' and paren_depth == 1:
            current_record.append(current_value.strip())
            current_value = ""
            i += 1
            continue
        elif paren_depth > 0:
            current_value += char

        i += 1

    return records


def clean_value(val):
    """Clean a parsed value."""
    if val is None:
        return ""
    val = str(val).strip()
    if val.upper() == 'NULL':
        return ""
    if val.startswith("_binary"):
        return ""
    if val.startswith("'") and val.endswith("'"):
        val = val[1:-1]
    val = val.replace("\\'", "'").replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
    return val


def load_data():
    """Load data from SQL dump file."""
    if DATA['loaded']:
        return

    print("Loading data from SQL dump...")

    with open(SQL_FILE, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            # Parse asset table
            if line.startswith("INSERT INTO `asset` VALUES"):
                print(f"  Parsing assets...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 9:
                        asset_id = clean_value(rec[0])
                        DATA['assets'][asset_id] = {
                            'PKAssetId': asset_id,
                            'FKAssetCategoryId': clean_value(rec[2]),
                            'FKBrandId': clean_value(rec[3]),
                            'FKModelId': clean_value(rec[4]),
                            'AssetName': clean_value(rec[5]),
                            'Comment': clean_value(rec[6]),
                            'IsActive': clean_value(rec[7]),
                            'FKOwnerId': clean_value(rec[8]),
                            'DateCreated': clean_value(rec[10]) if len(rec) > 10 else "",
                            'AssetLocation': clean_value(rec[11]) if len(rec) > 11 else "",
                            'AssetBlog': clean_value(rec[13]) if len(rec) > 13 else "",
                        }

            elif line.startswith("INSERT INTO `brand` VALUES"):
                print(f"  Parsing brands...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 2:
                        DATA['brands'][clean_value(rec[0])] = clean_value(rec[1])

            elif line.startswith("INSERT INTO `model` VALUES"):
                print(f"  Parsing models...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 3:
                        DATA['models'][clean_value(rec[0])] = clean_value(rec[2])

            elif line.startswith("INSERT INTO `assetcategory` VALUES"):
                print(f"  Parsing asset categories...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 3:
                        DATA['asset_categories'][clean_value(rec[0])] = clean_value(rec[2])

            elif line.startswith("INSERT INTO `assetcategoryfield` VALUES"):
                print(f"  Parsing asset category fields...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 2:
                        DATA['asset_category_fields'][clean_value(rec[0])] = clean_value(rec[1])

            elif line.startswith("INSERT INTO `mmassetfieldvalue` VALUES"):
                print(f"  Parsing asset field values...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 4:
                        asset_id = clean_value(rec[1])
                        field_id = clean_value(rec[2])
                        field_value = clean_value(rec[3])
                        field_name = DATA['asset_category_fields'].get(field_id, f"Field_{field_id}")
                        DATA['asset_field_values'][asset_id][field_name] = field_value

            elif line.startswith("INSERT INTO `customer` VALUES"):
                print(f"  Parsing customers...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 9:
                        cust_id = clean_value(rec[0])
                        first_name = clean_value(rec[6]) if len(rec) > 6 else ""
                        last_name = clean_value(rec[8]) if len(rec) > 8 else ""
                        company_name = clean_value(rec[50]) if len(rec) > 50 else ""

                        if last_name:
                            customer_name = f"{first_name} {last_name}".strip()
                        else:
                            customer_name = first_name

                        DATA['customers'][cust_id] = {
                            'CustomerName': customer_name,
                            'CompanyName': company_name,
                        }

            elif line.startswith("INSERT INTO `engineer` VALUES"):
                print(f"  Parsing engineers...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 8:
                        eng_id = clean_value(rec[0])
                        first_name = clean_value(rec[5]) if len(rec) > 5 else ""
                        last_name = clean_value(rec[7]) if len(rec) > 7 else ""
                        DATA['engineers'][eng_id] = f"{first_name} {last_name}".strip() if last_name else first_name

            elif line.startswith("INSERT INTO `assetupdate` VALUES"):
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 5:
                        asset_id = clean_value(rec[1])
                        DATA['asset_updates'][asset_id].append({
                            'user_id': clean_value(rec[2]),
                            'user_type': clean_value(rec[3]),
                            'date': clean_value(rec[4])
                        })

    DATA['loaded'] = True
    print(f"Data loaded: {len(DATA['assets'])} assets")


@app.route('/')
def index():
    """Main page with asset grid."""
    return render_template('index.html')


@app.route('/api/assets')
def get_assets():
    """API endpoint to get all assets for the grid."""
    load_data()

    assets_list = []
    for asset_id, asset in DATA['assets'].items():
        category = DATA['asset_categories'].get(asset['FKAssetCategoryId'], '')
        brand = DATA['brands'].get(asset['FKBrandId'], '')
        model = DATA['models'].get(asset['FKModelId'], '')
        customer_info = DATA['customers'].get(asset['FKOwnerId'], {})
        customer_name = customer_info.get('CustomerName', '')

        assets_list.append({
            'id': asset_id,
            'name': asset['AssetName'],
            'category': category,
            'brand': brand,
            'model': model,
            'customer': customer_name,
            'location': asset['AssetLocation']
        })

    return jsonify(assets_list)


@app.route('/api/asset/<asset_id>')
def get_asset_detail(asset_id):
    """API endpoint to get detailed asset information."""
    load_data()

    if asset_id not in DATA['assets']:
        return jsonify({'error': 'Asset not found'}), 404

    asset = DATA['assets'][asset_id]

    # Get lookups
    category = DATA['asset_categories'].get(asset['FKAssetCategoryId'], '')
    brand = DATA['brands'].get(asset['FKBrandId'], '')
    model = DATA['models'].get(asset['FKModelId'], '')
    customer_info = DATA['customers'].get(asset['FKOwnerId'], {})
    customer_name = customer_info.get('CustomerName', '')

    # Get created/updated info
    updates = sorted(DATA['asset_updates'].get(asset_id, []), key=lambda x: x['date'])
    created_by = ""
    updated_by = ""
    updated_date = ""

    if updates:
        first_update = updates[0]
        if first_update['user_type'] == '1':
            created_by = DATA['engineers'].get(first_update['user_id'], '')
        elif first_update['user_type'] == '2':
            cust = DATA['customers'].get(first_update['user_id'], {})
            created_by = cust.get('CustomerName', '')

        last_update = updates[-1]
        if last_update['user_type'] == '1':
            updated_by = DATA['engineers'].get(last_update['user_id'], '')
        elif last_update['user_type'] == '2':
            cust = DATA['customers'].get(last_update['user_id'], {})
            updated_by = cust.get('CustomerName', '')
        updated_date = last_update['date']

    # Get custom fields
    custom_fields = DATA['asset_field_values'].get(asset_id, {})

    return jsonify({
        'asset_info': {
            'Asset Name': asset['AssetName'],
            'Customer Name': customer_name,
            'Brand Name': brand,
            'Model Name': model,
            'Asset Category Name': category,
            'Created By': created_by,
            'Updated By': updated_by,
            'Created Date-Time': asset['DateCreated'],
            'Updated Date-Time': updated_date,
            'Location': asset['AssetLocation'],
            'Comment': asset['Comment'],
            'Asset Blog': asset['AssetBlog'],
        },
        'custom_fields': custom_fields
    })


if __name__ == '__main__':
    print("Starting Asset Viewer...")
    print("Loading data on first request...")
    app.run(debug=True, port=5001, host='127.0.0.1')
