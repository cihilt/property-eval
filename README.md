# Property Evaluation Dashboard

A comprehensive property intelligence dashboard that displays property data, price history, nearby schools, and area demographics.

## Features

- **Price History Chart**: Visual line graph showing property price trends over time
- **Property Summary**: AI-generated insights about the property and surrounding area
- **Price Statistics**: Latest, earliest, median, and average prices with growth percentage
- **Nearby Schools**: Complete list of schools with distances, types, and NAPLAN rankings
- **Area Demographics**: Visual breakdown of ethnic demographics in surrounding areas
- **Sales History**: Detailed table of all property transactions

<img width="1070" height="828" alt="image" src="https://github.com/user-attachments/assets/614c312b-7647-44f9-a471-b01063bc2153" />


## Installation

1. Install dependencies:
```bash
pip install flask flask-cors requests
```

2. Run the application:
```bash
python app.py
```

3. Open your browser to: http://127.0.0.1:5000/

## API Token

The application uses a sandbox API token (`test`) that works with demo property IDs like `GANSW704074813`. 

To use with real data, replace the `API_TOKEN` in `app.py` with your actual Microburbs API token.

## Project Structure

```
.
├── app.py                  # Flask backend with API endpoints
├── templates/
│   └── index.html         # Frontend dashboard
└── README.md
```

## Technologies Used

- **Backend**: Flask, Python
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **API**: Microburbs Property Data API
- **Charts**: Native SVG rendering
