import os
import sys
import csv
import time
from dotenv import load_dotenv

# Ensure the parent directory is in sys.path for module import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env file
load_dotenv()

from SalesforceRESTAPI import SalesforceRESTAPI

CLIENT_ID = os.getenv('SF_CLIENT_ID')
CLIENT_SECRET = os.getenv('SF_CLIENT_SECRET')
LOGIN_URL = os.getenv('SF_LOGIN_URL', 'https://login.salesforce.com')

# Authenticate with Salesforce
SalesforceRESTAPI.authenticate(CLIENT_ID, CLIENT_SECRET, LOGIN_URL)
sf = SalesforceRESTAPI()

def create_sample_csv():
    """
    Create a sample CSV file with Case data for testing.
    This CSV will contain the fields needed to create Cases in Salesforce.
    
    CSV columns:
    - Subject: The subject/title of the Case
    - Description: Details about the Case
    - Status: Current status (New, Working, Escalated, Closed)
    - Priority: Priority level (Low, Medium, High)
    - Origin: How the Case was created (Phone, Email, Web)
    """
    csv_filename = 'cases_to_create.csv'
    
    # Sample case data - modify as needed for your Salesforce org
    cases_data = [
        {
            'Subject': 'Website login issue',
            'Description': 'Customer cannot log in to the website',
            'Status': 'New',
            'Priority': 'High',
            'Origin': 'Email'
        },
        {
            'Subject': 'Product inquiry',
            'Description': 'Customer requesting information about pricing',
            'Status': 'New',
            'Priority': 'Medium',
            'Origin': 'Phone'
        },
        {
            'Subject': 'Technical support needed',
            'Description': 'Software installation problem',
            'Status': 'New',
            'Priority': 'High',
            'Origin': 'Web'
        },
        {
            'Subject': 'Billing question',
            'Description': 'Customer has questions about invoice',
            'Status': 'New',
            'Priority': 'Low',
            'Origin': 'Email'
        }
    ]
    
    # Write the CSV file
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Subject', 'Description', 'Status', 'Priority', 'Origin']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(cases_data)
    
    print(f"✓ Sample CSV file created: {csv_filename}")
    return csv_filename

def read_csv_to_string(csv_filename):
    """
    Read the CSV file and convert it to a string format required by Bulk API.
    The Bulk API expects the data as a CSV string in the request body.
    """
    with open(csv_filename, 'r', encoding='utf-8') as csvfile:
        csv_content = csvfile.read()
    return csv_content

def create_bulk_job():
    """
    Step 1: Create a bulk ingest job.
    This tells Salesforce we want to perform a bulk insert operation on Case objects.
    
    Returns:
        job_id: The unique identifier for this bulk job
    """
    # Define the job specification
    job_data = {
        "object": "Case",              # The Salesforce object type
        "operation": "insert",          # Operation type: insert, update, upsert, delete
        "contentType": "CSV"            # Data format: CSV or JSON
    }
    
    # Create the job using the Bulk API 2.0 endpoint
    response = sf.post("/services/data/v62.0/jobs/ingest", job_data)
    job_info = response.json()
    
    job_id = job_info['id']
    print(f"✓ Bulk job created with ID: {job_id}")
    print(f"  State: {job_info['state']}")
    
    return job_id

def upload_csv_data(job_id, csv_content):
    """
    Step 2: Upload the CSV data to the bulk job.
    This sends the actual Case records to Salesforce for processing.
    
    Args:
        job_id: The job ID from create_bulk_job()
        csv_content: The CSV data as a string
    """
    # Upload the CSV content
    # Note: We need to send the CSV as plain text, not JSON
    endpoint = f"/services/data/v62.0/jobs/ingest/{job_id}/batches"
    
    # The Bulk API expects CSV content with Content-Type: text/csv
    # We'll need to make a custom request since our post() method defaults to JSON
    headers = {
        **SalesforceRESTAPI.headers,
        'Content-Type': 'text/csv'
    }
    
    import requests
    url = f"{SalesforceRESTAPI.instance_url}{endpoint}"
    response = requests.put(url, headers=headers, data=csv_content)
    SalesforceRESTAPI.last_http_status = response.status_code
    
    if response.status_code in [200, 201]:
        print(f"✓ CSV data uploaded successfully to job {job_id}")
    else:
        print(f"✗ Upload failed: {response.text}")
        raise RuntimeError(f"Failed to upload data: {response.text}")

def close_bulk_job(job_id):
    """
    Step 3: Close the job to tell Salesforce we're done uploading data.
    Once closed, Salesforce will begin processing the records.
    
    Args:
        job_id: The job ID to close
    """
    endpoint = f"/services/data/v62.0/jobs/ingest/{job_id}"
    
    # Update job state to UploadComplete
    job_update = {
        "state": "UploadComplete"
    }
    
    response = sf.patch(endpoint, job_update)
    job_info = response.json()
    
    print(f"✓ Job {job_id} closed")
    print(f"  State: {job_info['state']}")

def check_job_status(job_id):
    """
    Step 4: Check the job status to see if processing is complete.
    The job will go through states: Open -> UploadComplete -> InProgress -> JobComplete
    
    Args:
        job_id: The job ID to check
        
    Returns:
        job_info: Dictionary containing job status and results
    """
    endpoint = f"/services/data/v62.0/jobs/ingest/{job_id}"
    
    response = sf.get(endpoint)
    job_info = response.json()
    
    print(f"\n--- Job Status for {job_id} ---")
    print(f"  State: {job_info['state']}")
    print(f"  Records Processed: {job_info.get('numberRecordsProcessed', 0)}")
    print(f"  Records Failed: {job_info.get('numberRecordsFailed', 0)}")
    print(f"  Total Processing Time (ms): {job_info.get('totalProcessingTime', 0)}")
    
    return job_info

def get_job_results(job_id):
    """
    Step 5: Get detailed results including successful and failed records.
    
    Args:
        job_id: The job ID to get results for
    """
    # Get successful records
    successful_endpoint = f"/services/data/v62.0/jobs/ingest/{job_id}/successfulResults"
    failed_endpoint = f"/services/data/v62.0/jobs/ingest/{job_id}/failedResults"
    
    print("\n--- Successful Records ---")
    success_response = sf.get(successful_endpoint)
    if success_response.text.strip():
        print(success_response.text)
    else:
        print("  No successful records or results not ready yet")
    
    print("\n--- Failed Records ---")
    failed_response = sf.get(failed_endpoint)
    if failed_response.text.strip():
        print(failed_response.text)
    else:
        print("  No failed records")

def test_bulk_create_cases():
    """
    Main function to demonstrate the complete Bulk API workflow:
    1. Create a sample CSV file
    2. Create a bulk job
    3. Upload CSV data to the job
    4. Close the job
    5. Poll for job completion
    6. Display results
    """
    try:
        print("=== Salesforce Bulk API - Create Cases from CSV ===\n")
        
        # Step 1: Create sample CSV file
        csv_filename = create_sample_csv()
        
        # Step 2: Read CSV content
        csv_content = read_csv_to_string(csv_filename)
        print(f"✓ CSV content loaded ({len(csv_content)} bytes)\n")
        
        # Step 3: Create bulk job
        job_id = create_bulk_job()
        print()
        
        # Step 4: Upload CSV data
        upload_csv_data(job_id, csv_content)
        print()
        
        # Step 5: Close the job (marks upload as complete)
        close_bulk_job(job_id)
        print()
        
        # Step 6: Poll for job completion
        print("Waiting for job to complete...")
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(2)  # Wait 2 seconds between checks
            job_info = check_job_status(job_id)
            
            # Check if job is complete
            if job_info['state'] in ['JobComplete', 'Failed', 'Aborted']:
                break
            
            attempt += 1
            print("  Still processing...")
        
        # Step 7: Get final results
        if job_info['state'] == 'JobComplete':
            print("\n✓ Job completed successfully!")
            get_job_results(job_id)
        else:
            print(f"\n✗ Job ended with state: {job_info['state']}")
        
        # Cleanup: optionally delete the CSV file
        # os.remove(csv_filename)
        
    except Exception as e:
        print(f"\n✗ Error during bulk operation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_bulk_create_cases()
