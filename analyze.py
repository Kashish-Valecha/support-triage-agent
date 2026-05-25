import csv

# Check for empty fields and inconsistencies
with open('support_tickets/output.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total rows: {len(rows)}\n")

empty_product_area = []
empty_status = []
empty_request_type = []

for i, row in enumerate(rows, 1):
    if not row['status'] or row['status'].strip() == '':
        empty_status.append(i)
    if not row['product_area'] or row['product_area'].strip() == '':
        empty_product_area.append(i)
    if not row['request_type'] or row['request_type'].strip() == '':
        empty_request_type.append(i)

print(f"Empty 'status' fields: {empty_status if empty_status else 'None'}")
print(f"Empty 'product_area' fields: {empty_product_area if empty_product_area else 'None'}")
print(f"Empty 'request_type' fields: {empty_request_type if empty_request_type else 'None'}\n")

# Check case inconsistency
statuses = set()
request_types = set()
for row in rows:
    statuses.add(row['status'])
    request_types.add(row['request_type'])

print(f"Unique status values: {sorted(statuses)}")
print(f"Unique request_type values: {sorted(request_types)}")

print(f"\n⚠️  CRITICAL ISSUES:\n")
print(f"1. CSV HEADERS are LOWERCASE: 'status', 'product_area', 'request_type'")
print(f"   But sample uses CAPITALIZED: 'Status', 'Product Area', 'Request Type'\n")
print(f"2. Status values are lowercase: {sorted(statuses)}")
print(f"   But sample uses capitalized: 'Replied', 'Escalated'\n")
print(f"3. product_area contains long descriptions (40+ chars)")
print(f"   Sample uses short categories: 'screen', 'community', etc.")
