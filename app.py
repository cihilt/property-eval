from flask import Flask, render_template, jsonify, request
import requests
from flask_cors import CORS
import concurrent.futures
import json
import math

app = Flask(__name__)
CORS(app)

# API Configuration
API_TOKEN = "test"  # Sandbox token for demo
API_BASE_URL = "https://www.microburbs.com.au/report_generator/api"
API_HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

@app.route('/')
def index():
    """Serve the main dashboard page"""
    return render_template('index.html')

@app.route('/api/property/<property_id>/complete')
def get_complete_property_data(property_id):
    """Fetch all property data in parallel"""

    def fetch_history():
        try:
            url = f"{API_BASE_URL}/property/history"
            response = requests.get(url, params={"id": property_id}, headers=API_HEADERS)
            response.raise_for_status()
            return response.json()
        except:
            return {"results": []}

    def fetch_summary():
        try:
            url = f"{API_BASE_URL}/property/summary"
            response = requests.get(url, params={"id": property_id}, headers=API_HEADERS)
            response.raise_for_status()
            return response.json()
        except:
            return {}

    def fetch_schools():
        try:
            url = f"{API_BASE_URL}/property/schools"
            response = requests.get(url, params={"id": property_id}, headers=API_HEADERS)
            response.raise_for_status()
            return response.json()
        except:
            return {"results": []}

    def fetch_ethnicity():
        try:
            url = f"{API_BASE_URL}/property/ethnicity"
            response = requests.get(url, params={"id": property_id}, headers=API_HEADERS)
            response.raise_for_status()
            return response.json()
        except:
            return {"results": []}

    # Fetch all data in parallel for speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_history = executor.submit(fetch_history)
        future_summary = executor.submit(fetch_summary)
        future_schools = executor.submit(fetch_schools)
        future_ethnicity = executor.submit(fetch_ethnicity)

        history_data = future_history.result()
        summary_data = future_summary.result()
        schools_data = future_schools.result()
        ethnicity_data = future_ethnicity.result()

    # Calculate price statistics from history
    price_stats = calculate_property_summary(history_data.get('results', []))

    # Process schools data
    schools_summary = process_schools_data(schools_data.get('results', []))

    # Process ethnicity data
    ethnicity_summary = process_ethnicity_data(ethnicity_data.get('results', []))

    # Clean NaN values from schools data
    schools_clean = clean_nan_values(schools_data.get('results', []))

    return jsonify({
        "success": True,
        "property_id": property_id,
        "history": history_data.get('results', []),
        "price_stats": price_stats,
        "summary": summary_data.get('summary', ''),
        "summary_points": summary_data.get('summary_points', ''),
        "summary_short": summary_data.get('summary_short', ''),
        "schools": schools_clean,
        "schools_summary": schools_summary,
        "ethnicity": ethnicity_data.get('results', []),
        "ethnicity_summary": ethnicity_summary
    })

@app.route('/api/property/<property_id>')
def get_property_history(property_id):
    """Fetch property history for a specific property ID"""
    try:
        url = f"{API_BASE_URL}/property/history"
        params = {"id": property_id}
        response = requests.get(url, params=params, headers=API_HEADERS)
        response.raise_for_status()
        data = response.json()

        if 'results' in data and len(data['results']) > 0:
            # Calculate summary statistics from history
            summary = calculate_property_summary(data['results'])
            return jsonify({
                "success": True,
                "property_id": property_id,
                "history": data['results'],
                "summary": summary
            })
        else:
            return jsonify({
                "success": False,
                "error": "No history found for this property",
                "history": [],
                "summary": {}
            })
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "history": [],
            "summary": {}
        }), 500

def calculate_property_summary(history):
    """Calculate summary statistics from property history"""
    if not history:
        return {}

    # Initialize data
    prices = []
    sale_types = {}
    dates = []

    # Extract data
    for record in history:
        # Price
        if 'price' in record and record['price']:
            try:
                price = float(record['price'])
                prices.append(price)
            except:
                pass

        # Sale type
        sale_type = record.get('type', 'Unknown')
        sale_types[sale_type] = sale_types.get(sale_type, 0) + 1

        # Dates
        if 'date' in record and record['date']:
            dates.append(record['date'])

    # Calculate statistics
    summary = {
        "total_records": len(history),
        "address": history[0].get('address', 'Unknown'),
        "sale_types": sale_types
    }

    if prices:
        prices.sort()
        summary["latest_price"] = prices[-1]
        summary["earliest_price"] = prices[0]
        summary["median_price"] = prices[len(prices) // 2]
        summary["avg_price"] = sum(prices) / len(prices)
        summary["min_price"] = min(prices)
        summary["max_price"] = max(prices)

        # Calculate price growth if we have multiple prices
        if len(prices) > 1:
            price_growth = ((prices[-1] - prices[0]) / prices[0]) * 100
            summary["price_growth_percent"] = round(price_growth, 2)

    if dates:
        dates.sort()
        summary["earliest_date"] = dates[0]
        summary["latest_date"] = dates[-1]

    return summary

def process_schools_data(schools):
    """Process schools data to extract key statistics"""
    if not schools:
        return {}

    total_schools = len(schools)
    catchment_schools = len([s for s in schools if s.get('in_catchment') == 'Yes'])

    # Separate by type
    primary = [s for s in schools if 'Primary' in s.get('school_level_type', '')]
    secondary = [s for s in schools if 'Secondary' in s.get('school_level_type', '')]
    combined = [s for s in schools if 'Combined' in s.get('school_level_type', '')]

    # Public vs Private
    public = [s for s in schools if s.get('school_sector_type') == 'Public']
    private = [s for s in schools if s.get('school_sector_type') == 'Private']

    # Average distance
    distances = [s.get('distance', 0) for s in schools if s.get('distance')]
    avg_distance = sum(distances) / len(distances) if distances else 0

    return {
        "total_schools": total_schools,
        "in_catchment": catchment_schools,
        "primary": len(primary),
        "secondary": len(secondary),
        "combined": len(combined),
        "public": len(public),
        "private": len(private),
        "avg_distance_meters": round(avg_distance)
    }

def process_ethnicity_data(ethnicity_data):
    """Process ethnicity data to get top ethnicities"""
    if not ethnicity_data:
        return {}

    # Aggregate all ethnicity percentages
    ethnicity_totals = {}

    for area in ethnicity_data:
        for ethnicity, percentage in area.get('ethnicity', {}).items():
            if ethnicity not in ethnicity_totals:
                ethnicity_totals[ethnicity] = []
            ethnicity_totals[ethnicity].append(percentage)

    # Calculate averages
    ethnicity_averages = {
        ethnicity: sum(values) / len(values)
        for ethnicity, values in ethnicity_totals.items()
    }

    # Sort by percentage
    sorted_ethnicities = sorted(
        ethnicity_averages.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return {
        "top_ethnicities": sorted_ethnicities[:5],
        "total_areas": len(ethnicity_data)
    }

def clean_nan_values(data):
    """Recursively clean NaN values from data structures"""
    if isinstance(data, list):
        return [clean_nan_values(item) for item in data]
    elif isinstance(data, dict):
        return {key: clean_nan_values(value) for key, value in data.items()}
    elif isinstance(data, float) and math.isnan(data):
        return None
    else:
        return data

if __name__ == '__main__':
    app.run(debug=True, port=5000)
