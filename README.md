# SalesforceRESTAPI

A simple Python library to interact with the Salesforce REST API using OAuth 2.0 Client Credentials Flow.

## Features
- Authenticate with Salesforce using OAuth 2.0 Client Credentials
- Basic CRUD operations (create, read, update, delete) for Salesforce objects
- Bulk API 2.0 support for inserting large datasets
- SOQL query support
- Apex script execution via Tooling API
- Record verification utilities
- HTTP status code tracking for all API requests

## Installation

```bash
pip install SalesforceRESTAPI
```

## Usage

> **Note:** As of version 0.1.3, authentication state (`instance_url`, `access_token`, `headers`) is stored as class variables. You must call `SalesforceRESTAPI.authenticate(...)` before using any instance methods. All instances share the same authentication state.

```python
from SalesforceRESTAPI import SalesforceRESTAPI

# Authenticate (call this once before using any instance methods)
SalesforceRESTAPI.authenticate(client_id='YOUR_CLIENT_ID', client_secret='YOUR_CLIENT_SECRET', login_url='https://login.salesforce.com')

# Now you can use instance methods
sf = SalesforceRESTAPI()

# Create a record
account_id = sf.create_record('Account', Name='Test Account', Industry='Technology')

# Get a record
account = sf.get_record('Account', account_id)

# Update a record
sf.update_record('Account', account_id, Name='Updated Name')

# Delete a record
sf.delete_record('Account', account_id)

# Run a SOQL query
results = sf.queryRecords('SELECT Id, Name FROM Account')

# Execute anonymous Apex
apex_result = sf.execute_apex('System.debug("Hello World");')

# Bulk insert records (for large datasets)
records = [
    {'Subject': 'Test Case 1', 'Status': 'New', 'Priority': 'Medium'},
    {'Subject': 'Test Case 2', 'Status': 'New', 'Priority': 'High'},
    {'Subject': 'Test Case 3', 'Status': 'New', 'Priority': 'Low'}
]
result = sf.bulk_insert_records('Case', records)
print(f"Job ID: {result['job_id']}, Records Processed: {result['records_processed']}")

# Get last HTTP status code
status_code = SalesforceRESTAPI.get_last_http_status()
print(f"Last HTTP Status: {status_code}")

# Revoke authentication (clears class-level state)
sf.revoke()
```

## Requirements
- Python 3.6+
- requests
- python-dotenv (for loading .env files in tests)

## License
MIT License. See [LICENSE](LICENSE) for details.
