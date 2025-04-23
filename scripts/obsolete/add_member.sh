#!/bin/bash

# Define the API endpoint URL
API_URL="https://demo.quome.cloud/api/v1/orgs/86880079-c52c-4e5f-9501-101f8a779c66/members"

# Define the JSON payload
payload='{
  "user_id": "955fbfaa-a99c-448f-bd87-738d7a757039"
}'

# Define the Bearer token
TOKEN="XAE-RjI-jjdH1CYFCSHS382sOIoery6QPymRhfw7fFA.GVHZIXs_6mRXasmuN1hFGqXe27QCyKSXsj4y_8_yKAE"

# Send the POST request using curl with the Authorization header
curl -k -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d "$payload"
