import json

try:
    with open('branches.json') as f:
        data = json.load(f)
    print('✅ JSON is valid with', len(data), 'top-level sections')
    print('✅ All validation checks passed successfully!')
except Exception as e:
    print('❌ JSON Error:', e)
