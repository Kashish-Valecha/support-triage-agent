import csv

data = []
with open('support_tickets/output.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)

# Display table
print('=== FULL OUTPUT.CSV ===\n')
print(f'Total rows: {len(data)}\n')

for i, row in enumerate(data, 1):
    print(f'Row {i}:')
    print(f'  Status: {row["Status"]}')
    print(f'  Product Area: {row["Product Area"]} (len: {len(row["Product Area"])})')
    response_preview = row["Response"][:70] + '...' if len(row['Response']) > 70 else row["Response"]
    print(f'  Response: {response_preview}')
    just_preview = row["Justification"][:60] + '...' if len(row['Justification']) > 60 else row["Justification"]
    print(f'  Justification: {just_preview}')
    print(f'  Request Type: {row["Request Type"]}')
    print()

# Analysis
print('\n=== VALIDATION ANALYSIS ===\n')

# 1. Check for empty Response or Justification
empty_response = sum(1 for row in data if not row['Response'].strip())
empty_justification = sum(1 for row in data if not row['Justification'].strip())
print(f'1) Empty cells:')
print(f'   ✓ Empty Response: {empty_response}')
print(f'   ✓ Empty Justification: {empty_justification}')

# 2. Count Replied vs Escalated
replied = sum(1 for row in data if row['Status'] == 'Replied')
escalated = sum(1 for row in data if row['Status'] == 'Escalated')
print(f'\n2) Status breakdown:')
print(f'   ✓ Replied: {replied}')
print(f'   ✓ Escalated: {escalated}')
print(f'   - Percentage: {replied}/{len(data)} ({100*replied//len(data)}% replied)')

# 3. Check for invalid request_type
valid_types = {'product_issue', 'feature_request', 'bug', 'invalid'}
invalid_count = 0
invalid_types = []
for row in data:
    if row['Request Type'].lower() not in valid_types:
        invalid_count += 1
        invalid_types.append((data.index(row) + 1, row['Request Type']))

print(f'\n3) Request Type validation:')
print(f'   ✓ Valid types: {len(data) - invalid_count}')
print(f'   ✓ Invalid types: {invalid_count}')
if invalid_types:
    for row_num, invalid_type in invalid_types:
        print(f'   - Row {row_num}: "{invalid_type}"')

# 4. Check Product Area length
long_areas = []
for i, row in enumerate(data):
    if len(row['Product Area']) > 20:
        long_areas.append((i+1, row['Product Area'], len(row['Product Area'])))

print(f'\n4) Product Area length check:')
print(f'   ✓ Areas within 20 chars: {len(data) - len(long_areas)}')
print(f'   ✓ Areas over 20 chars: {len(long_areas)}')
if long_areas:
    for row_num, area, length in long_areas:
        print(f'   - Row {row_num}: "{area}" ({length} chars)')

# Summary
print('\n=== SUMMARY ===')
issues = empty_response + empty_justification + invalid_count + len(long_areas)
if issues == 0:
    print('✅ All checks passed! Data is valid and ready for submission.')
else:
    print(f'⚠️  Found {issues} issues to address.')
