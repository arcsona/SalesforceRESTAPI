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

## Query All (pagination helper)

`query_all` is a convenience method that wraps the REST `/queryAll` endpoint and automatically pages through `nextRecordsUrl` to return all matching records (including archived/deleted when supported).

Usage:

```python
# Run a SOQL using queryAll and retrieve all pages
soql = "SELECT Id, Name FROM Account WHERE CreatedDate > LAST_N_DAYS:365"
result = sf.query_all(soql)
print(f"Total records: {result['totalSize']}")
for rec in result['records'][:10]:
    print(rec.get('Id'), rec.get('Name'))
```

Return value:
- A dict with keys: `totalSize` (int) and `records` (list of record dicts).
- The method follows `nextRecordsUrl` until all pages are fetched.

Notes:
- Use `query_all` when you expect many results or need deleted/archived records. For small queries, `run_query`/`queryRecords` is sufficient.
- Make sure `SalesforceRESTAPI.authenticate(...)` is called first so class-level auth state is set.


## Robot Framework Usage

You can use this library from Robot Framework by importing it as a Python library in your test suite. Below are the minimal steps to integrate:

1. Install the package into the same Python environment used by Robot Framework:

```bash
# activate your virtualenv, then
pip install SalesforceRESTAPI
pip install robotframework
```

2. Create a simple Robot Framework resource or test that imports the Python module. Example `salesforce.robot`:

```robot
*** Settings ***
Library    SalesforceRESTAPI

*** Variables ***
${CLIENT_ID}      your_client_id
${CLIENT_SECRET}  your_client_secret
${LOGIN_URL}      https://login.salesforce.com

*** Test Cases ***
Bulk Create Cases From List
    # Authenticate using class method (sets class-level state)
    Evaluate    SalesforceRESTAPI.authenticate('${CLIENT_ID}', '${CLIENT_SECRET}', '${LOGIN_URL}')    modules=SalesforceRESTAPI
    ${sf}=    Evaluate    SalesforceRESTAPI.SalesforceRESTAPI()    modules=SalesforceRESTAPI
    @{records}=    Create List
    ...    {'Subject': 'RF Case 1', 'Status': 'New', 'Priority': 'Medium'}
    ...    {'Subject': 'RF Case 2', 'Status': 'New', 'Priority': 'High'}
    ${result}=    Evaluate    ${sf}.bulk_insert_records('Case', ${records}, wait_for_completion=True, max_wait_seconds=60)    modules=SalesforceRESTAPI
    Log    Job ID: ${result['job_id']} | State: ${result['state']}
```

Notes:
- We use `Evaluate` to call class methods and instance methods from Robot; alternatively you can wrap small helper keywords in a custom Robot library that calls into `SalesforceRESTAPI`.
- Ensure the Robot process uses the same virtual environment where `SalesforceRESTAPI` is installed so dependencies like `requests` and `python-dotenv` are available.


## Requirements
- Python 3.6+
- requests
- python-dotenv (for loading .env files in tests)

## License
MIT License. See [LICENSE](LICENSE) for details.
