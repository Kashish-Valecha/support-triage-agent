import csv

print('=== SAMPLE EXPECTED FORMAT (first 5 rows) ===\n')
with open('support_tickets/sample_support_tickets.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i >= 5:
            break
        print(f"Row {i+1}:")
        print(f"  Status: '{row['Status']}'")
        print(f"  Product Area: '{row['Product Area']}'")
        print(f"  Request Type: '{row['Request Type']}'")
        print()

print('=== AGENT OUTPUT (first 5 rows) ===\n')
with open('support_tickets/output.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i >= 5:
            break
        print(f"Row {i+1}:")
        print(f"  Status: '{row['Status']}'")
        print(f"  Product Area: '{row['Product Area']}'")
        print(f"  Request Type: '{row['Request Type']}'")
        if not row['Status'] or not row['Product Area']:
            print(f"  ⚠️  EMPTY FIELD DETECTED")
        print()
