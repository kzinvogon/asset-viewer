#!/usr/bin/env python3
"""
Export parsed SQL data to JSON for Railway deployment
"""

import re
import json
from collections import defaultdict

SQL_FILE = "/Users/davidhamilton/Dev/Ai Apoyar Source Data /apoyar_db.sql"
OUTPUT_FILE = "/Users/davidhamilton/Dev/Ai Apoyar Source Data /asset_viewer/data.json"


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


def main():
    print("Reading SQL dump file...")

    data = {
        'assets': {},
        'asset_categories': {},
        'brands': {},
        'models': {},
        'asset_category_fields': {},
        'asset_field_values': defaultdict(dict),
        'customers': {},
        'engineers': {},
        'asset_updates': defaultdict(list),
    }

    with open(SQL_FILE, 'r', encoding='utf-8', errors='replace') as f:
        for line_num, line in enumerate(f, 1):
            if line.startswith("INSERT INTO `asset` VALUES"):
                print(f"  Parsing assets...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 9:
                        asset_id = clean_value(rec[0])
                        data['assets'][asset_id] = {
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
                        data['brands'][clean_value(rec[0])] = clean_value(rec[1])

            elif line.startswith("INSERT INTO `model` VALUES"):
                print(f"  Parsing models...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 3:
                        data['models'][clean_value(rec[0])] = clean_value(rec[2])

            elif line.startswith("INSERT INTO `assetcategory` VALUES"):
                print(f"  Parsing asset categories...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 3:
                        data['asset_categories'][clean_value(rec[0])] = clean_value(rec[2])

            elif line.startswith("INSERT INTO `assetcategoryfield` VALUES"):
                print(f"  Parsing asset category fields...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 2:
                        data['asset_category_fields'][clean_value(rec[0])] = clean_value(rec[1])

            elif line.startswith("INSERT INTO `mmassetfieldvalue` VALUES"):
                print(f"  Parsing asset field values...")
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 4:
                        asset_id = clean_value(rec[1])
                        field_id = clean_value(rec[2])
                        field_value = clean_value(rec[3])
                        field_name = data['asset_category_fields'].get(field_id, f"Field_{field_id}")
                        data['asset_field_values'][asset_id][field_name] = field_value

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

                        data['customers'][cust_id] = {
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
                        data['engineers'][eng_id] = f"{first_name} {last_name}".strip() if last_name else first_name

            elif line.startswith("INSERT INTO `assetupdate` VALUES"):
                records = parse_insert_values(line)
                for rec in records:
                    if len(rec) >= 5:
                        asset_id = clean_value(rec[1])
                        data['asset_updates'][asset_id].append({
                            'user_id': clean_value(rec[2]),
                            'user_type': clean_value(rec[3]),
                            'date': clean_value(rec[4])
                        })

    # Convert defaultdicts to regular dicts for JSON serialization
    data['asset_field_values'] = dict(data['asset_field_values'])
    data['asset_updates'] = dict(data['asset_updates'])

    print(f"\nFound {len(data['assets'])} assets")
    print(f"Writing to {OUTPUT_FILE}...")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    print("Done!")


if __name__ == "__main__":
    main()
