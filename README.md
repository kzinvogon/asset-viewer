# Asset Viewer - Apoyar CMDB

A web-based utility to view and browse assets from the Apoyar database. Parses MySQL dump files and displays assets in a searchable, sortable grid with detailed information panels.

## Features

- **Searchable Grid**: Browse all assets with real-time search filtering
- **Sortable Columns**: Click column headers to sort by any field
- **Detail Panel**: Click any row to view comprehensive asset information
- **Custom Fields**: Displays all additional asset information fields
- **No Database Required**: Reads directly from SQL dump files

## Screenshot

The main interface displays:
- **Grid View**: ID, Asset Name, Asset Category, Brand Name, Model Name, Customer Name, Location
- **Detail Panel**: Full asset information including comments, blog entries, and all custom fields

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/asset-viewer.git
cd asset-viewer
```

2. Create a virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure the SQL file path in `app.py`:
```python
SQL_FILE = "/path/to/your/database.sql"
```

## Usage

### Start the server:
```bash
./start.sh
```
Or manually:
```bash
source venv/bin/activate
python app.py
```

### Access the application:
Open your browser to: **http://127.0.0.1:5001**

## Project Structure

```
asset_viewer/
├── app.py              # Flask application and SQL parser
├── start.sh            # Startup script
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── templates/
    └── index.html      # Web interface with DataTables grid
```

## Configuration

Edit `app.py` to change:
- `SQL_FILE`: Path to your MySQL dump file
- `port`: Server port (default: 5001)

## Data Format

The application parses standard MySQL dump files containing these tables:
- `asset` - Main asset records
- `assetcategory` - Asset categories
- `brand` - Brand names
- `model` - Model names
- `customer` - Customer information
- `engineer` - Engineer/user information
- `assetcategoryfield` - Custom field definitions
- `mmassetfieldvalue` - Custom field values
- `assetupdate` - Update history

## License

MIT License

## Author

Generated with Claude Code
