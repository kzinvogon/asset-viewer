#!/usr/bin/env python3
"""
Asset Viewer Web Application
Displays assets from pre-parsed JSON data in a searchable grid with detail view
"""

from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

# Global data storage
DATA = {
    'assets': {},
    'asset_categories': {},
    'brands': {},
    'models': {},
    'asset_category_fields': {},
    'asset_field_values': {},
    'customers': {},
    'engineers': {},
    'asset_updates': {},
    'loaded': False
}

# Data file path (JSON file bundled with app)
DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')


def load_data():
    """Load data from JSON file."""
    if DATA['loaded']:
        return

    print("Loading data from JSON file...")

    if not os.path.exists(DATA_FILE):
        print(f"Warning: Data file not found at {DATA_FILE}")
        DATA['loaded'] = True
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        loaded = json.load(f)
        DATA['assets'] = loaded.get('assets', {})
        DATA['asset_categories'] = loaded.get('asset_categories', {})
        DATA['brands'] = loaded.get('brands', {})
        DATA['models'] = loaded.get('models', {})
        DATA['asset_category_fields'] = loaded.get('asset_category_fields', {})
        DATA['asset_field_values'] = loaded.get('asset_field_values', {})
        DATA['customers'] = loaded.get('customers', {})
        DATA['engineers'] = loaded.get('engineers', {})
        DATA['asset_updates'] = loaded.get('asset_updates', {})

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
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port, host='0.0.0.0')
