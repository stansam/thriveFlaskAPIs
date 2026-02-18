API Overview
The Kayak Flight Search API is a powerful, unofficial travel API that allows developers to integrate Kayak-style flight search and price comparison functionality into web and mobile applications.

This flight search API provides access to real-time airline data, including available routes, flight schedules, pricing insights, and live availability aggregated from multiple global travel sources. Developers can use the API to build flight tracking tools, travel comparison platforms, and booking workflows with accurate and up-to-date data.

Designed for scalability and performance, the API supports advanced flight comparison features such as searching, filtering, and sorting flights by price, airline, duration, and departure time - similar to the experience offered by leading travel metasearch platforms like Kayak.

The API is ideal for:

Flight search engines
Travel booking platforms
Airline price comparison websites
Travel startups and SaaS products
Deal aggregation and monitoring tools
Beyond flight search, the API architecture supports future expansion into hotel search, car rentals, and vacation stays. This makes it a flexible foundation for building multi-modal travel and transportation applications using a unified travel data API.

Whether you are building a custom flight search engine, enhancing an existing travel booking platform, or experimenting with airline price monitoring tools, the Kayak Flight Search API provides a reliable, developer-friendly solution for accessing global travel data through RapidAPI.

Kayak Flight and transportation API for developers access real-time flight routes, airline schedules, prices, and availability via RapidAPI. Build flight comparison, tracking, and booking apps using Kayak-style global travel data.

Kayak Flight & Car Search API
📡 API Endpoints

1. Flight Search
2. Car Rental Search
3. Location Search

---

## ✈️ Flight Search API

### Required Parameters

| Parameter        | Type   | Description                 | Example                   |
| ---------------- | ------ | --------------------------- | ------------------------- |
| `origin`         | string | Origin airport code         | `"MIA"`, `"LAX"`, `"LON"` |
| `destination`    | string | Destination airport code    | `"NYC"`, `"JFK"`, `"LHR"` |
| `departure_date` | string | Departure date (YYYY-MM-DD) | `"2025-10-25"`            |

### Optional Parameters

| Parameter          | Type   | Description                            |
| ------------------ | ------ | -------------------------------------- |
| `return_date`      | string | Return date for round-trip             |
| `filterParams`     | object | Filters (airlines, price, stops, etc.) |
| `searchMetaData`   | object | Pagination, pricing mode               |
| `userSearchParams` | object | Passengers, cabin class, sort mode     |

---

## 👥 Passenger Types & Cabin Classes

### Passenger Types

Configure passengers in `userSearchParams.passengers` as an array:

| Code  | Type                 | Age/Description |
| ----- | -------------------- | --------------- |
| `ADT` | Adults               | 18-64 years     |
| `SNR` | Seniors              | Over 65 years   |
| `STD` | Students             | Over 18 years   |
| `YTH` | Youths               | 12-17 years     |
| `CHD` | Children             | 2-11 years      |
| `INS` | Toddlers in own seat | Under 2 years   |
| `INL` | Infants on lap       | Under 2 years   |

**Example - 2 Adults + 1 Child:**

```json
{
  "userSearchParams": {
    "passengers": ["ADT", "ADT", "CHD"]
  }
}
Example - Family Travel:

{
  "userSearchParams": {
    "passengers": ["ADT", "ADT", "YTH", "CHD", "INL"]
  }
}
Cabin Classes
Specify cabin in filterParams.fs or in structured format:

Cabin	Code	Filter String
Economy	e	cabin=e
Premium Economy	p	cabin=p
Business	b	cabin=b
First	f	cabin=f
Example - Business Class:

{
  "filterParams": {
    "fs": "cabin=b"
  }
}
Note: Cabin filtering via API is not 100% reliable. It's better to filter results client-side.

📋 Example Requests
1. One-Way Flight
{
  "origin": "MIA",
  "destination": "NYC",
  "departure_date": "2025-10-25"
}
2. Round-Trip
{
  "origin": "LAX",
  "destination": "JFK",
  "departure_date": "2025-11-01",
  "return_date": "2025-11-10"
}
3. With Filters (Nonstop, Under $500)
{
  "origin": "LAX",
  "destination": "JFK",
  "departure_date": "2025-11-01",
  "filterParams": {
    "fs": "stops=0;price=-500"
  }
}
4. Advanced (Multiple Filters + Sort)
{
  "origin": "LON",
  "destination": "NYC",
  "departure_date": "2025-10-20",
  "return_date": "2025-10-25",
  "filterParams": {
    "fs": "airlines=-OS;stops=-1;price=-2000;alliance=STAR_ALLIANCE"
  },
  "searchMetaData": {
    "pageNumber": 1
  },
  "userSearchParams": {
    "sortMode": "price_a"
  }
}
5. With Specific Passengers
{
  "origin": "JFK",
  "destination": "CDG",
  "departure_date": "2025-12-20",
  "return_date": "2026-01-05",
  "userSearchParams": {
    "passengers": ["ADT", "ADT", "YTH", "CHD", "INL"]
  }
}
2 Adults + 1 Youth (12-17) + 1 Child (2-11) + 1 Infant on lap

6. Business Class with Multiple Passengers
{
  "origin": "SFO",
  "destination": "LHR",
  "departure_date": "2025-11-15",
  "return_date": "2025-11-25",
  "filterParams": {
    "fs": "cabin=b;stops=0"
  },
  "userSearchParams": {
    "passengers": ["ADT", "ADT"]
  }
}
Business class, nonstop, 2 adults

🔍 Filter String (fs) Reference
All filters go in filterParams.fs as semicolon-separated values:

Filter	Syntax	Example
Airlines	airlines=CODE or -CODE	airlines=-OS,-BA (exclude)
Airports	airports=CODE or -CODE	airports=-LGA,-LGW (exclude)
Stops	stops=NUM or -NUM	stops=0 (nonstop only)
Price	price=-MAX or MIN-MAX	price=-500 (under $500)
Duration	legdur=-MAX (minutes)	legdur=-600 (under 10h)
Layover	layoverdur=MIN- (minutes)	layoverdur=120- (min 2h)
Alliance	alliance=NAME	alliance=STAR_ALLIANCE
Same Airline	sameair=sameair	sameair=sameair
Equipment	equipment=TYPE or -TYPE	equipment=W (wide-body)
WiFi	wifi=wifi	wifi=wifi
Combine filters:

"fs": "airlines=-OS;stops=0;price=-500;alliance=STAR_ALLIANCE"
🎯 Sort Options
Set in userSearchParams.sortMode:

Mode	Description
price_a	Price ascending (cheapest first)
duration_a	Duration ascending (shortest first)
bestflight_a	Best overall (default)
departure_a	Earliest departure
arrival_a	Earliest arrival
```
