GET /search-locations
Examples:

# Find airports in Miami

GET /search-locations?query=miami

# Find airports in New York

GET /search-locations?query=new+york

# Find specific airport

GET /search-locations?query=LAX&type=airportonly

Response Format:
`{
  "success": true,
  "error": null,
  "data": {
    "query": "miami",
    "count": 1,
    "results": [
      {
        "id": "MIA",
        "airportname": "Miami",
        "cityname": "Miami, Florida, United States",
        "displayname": "Miami (MIA - Miami Intl.)",
        "city": "Miami",
        "state": "Florida",
        "country": "United States",
        "countrycode": "US",
        "lat": 25.79325,
        "lng": -80.29056,
        "timezone": "America/New_York"
      }
    ]
  }
}`
