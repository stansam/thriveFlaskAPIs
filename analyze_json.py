import json

def get_schema(obj, depth=0, max_depth=5):
    if depth > max_depth:
        return "..."
    if isinstance(obj, dict):
        return {k: get_schema(v, depth+1, max_depth) for k, v in obj.items()}
    elif isinstance(obj, list):
        if not obj:
            return []
        return [get_schema(obj[0], depth+1, max_depth)]
    else:
        return type(obj).__name__

print("=== FLIGHT DETAILS SCHEMA ===")
with open('flightDetailsResp.json') as f:
    data = json.load(f)
    print(json.dumps(get_schema(data, max_depth=4), indent=2))

print("\n=== FLIGHT SEARCH SCHEMA ===")
with open('flightSearchResp.json') as f:
    data = json.load(f)
    print(json.dumps(get_schema(data, max_depth=2), indent=2))
