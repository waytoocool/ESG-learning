#!/bin/bash
# Simple test using curl

# Login to get session cookie
echo "Logging in..."
SESSION=$(curl -s -c cookies.txt -b cookies.txt \
  -X POST http://test-company-alpha.127-0-0-1.nip.io:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=alice@alpha.com&password=admin123" \
  | grep -o 'session=[^;]*' | head -1)

echo "Session: $SESSION"

# Try to assign field to both entities (2 and 3), where 3 already has assignment
echo -e "\nTrying to assign field 054dd45e-9265-4527-9206-09fab8886863 to entities [2, 3]..."
curl -s -b cookies.txt \
  -X POST http://test-company-alpha.127-0-0-1.nip.io:8000/admin/assign_entities \
  -H "Content-Type: application/json" \
  -d '{
    "field_ids": ["054dd45e-9265-4527-9206-09fab8886863"],
    "entity_ids": [2, 3],
    "configuration": {
      "frequency": "Monthly",
      "unit": null,
      "assigned_topic_id": null
    }
  }' | python3 -m json.tool
