import imaplib
import email
from email.header import decode_header
from openai import OpenAI
import requests
import certifi
import httpx

def check_email():
    # Connect to IMAP server
    server = ''
    username = ''
    password = ''

    mail = imaplib.IMAP4_SSL(server)
    mail.login(username, password)

    # Select inbox
    mail.select("inbox")

    # Search for unread emails
    status, messages = mail.search(None, 'UNSEEN')

    for num in messages[0].split():
        status, data = mail.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Extract email details
        subject = decode_header(msg["Subject"])[0][0]
        sender = msg.get("From")
        print(f"New email from {sender}: {subject}")
        process_email(msg)

    mail.close()
    mail.logout()


def process_email(msg):
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            print("Body:", part.get_payload(decode=True).decode())
        elif part.get_content_disposition() == "attachment":
            filename = part.get_filename()
            if filename:
                with open(filename, "wb") as f:
                    f.write(part.get_payload(decode=True))
                print(f"Attachment saved: {filename}")

# Azure OpenAI endpoint and API key
url = ""
api_key = ""


def query_chatgpt(prompt):
    # Request headers
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    params = {
        "api-version": "2023-03-15-preview"
    }
    # Request body
    data = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": f"{prompt}"
            }
        ]
    }
    # Sending POST request to Azure OpenAI API
    try:
        response = requests.post(url, params=params, headers=headers, json=data)
        response.raise_for_status()  # Raise HTTPError for bad responses
        result = response.json()
        print(result["choices"][0]["message"]["content"])  # Extract assistant's reply
    except requests.exceptions.RequestException as e:
        print(f"Error querying Azure OpenAI: {e}")

def generate_prompt(text):
    return f"""
    Extract and fill the following fields based on the provided text. If data is missing, respond with null and put all the fields in a map. Give only the map in response

    Fields:
    1. Ledger ID
    2. Policy Type
    3. Policy Number
    4. Claim ID
    5. Claimant Name
    6. Phone Number
    7. Email ID
    8. Aadhar ID
    9. Abha ID
    10. Insurer Name
    11. Claim Status
    12. Claim Date
    13. Claim Amount (₹)
    14. Settlement Amount (₹)
    15. Settlement Date
    16. Fraud Score (%)
    17. Pincode
    18. City
    19. State
    20. Vehicle Registration No.
    21. Vehicle Type
    22. Vehicle Make and Model
    23. Car/Bike Age
    24. Accident Date
    25. Accident Location
    26. Garage Name
    27. Repair Estimate (₹)
    28. Driving Behavior Data
    29. Hospital Name
    30. Diagnosis/Illness
    31. Hospitalization Start Date
    32. Hospitalization End Date
    33. Total Medical Expenses (₹)
    34. Pre-Approved Amount (₹)
    35. Hospital Bills
    36. Test Reports
    37. Initial Analysis
    38. Final Analysis
    39. Travel Dates
    40. Trip Destination
    41. Flight Details
    42. Reason for Claim
    43. Nominee Name
    44. Policy Coverage (₹)
    45. Cause Proof
    46. Cause Statement
    47. IoT Data Available
    48. Third-Party Involvement
    49. Error Codes
    50. Claim Processing Time
    51. Supporting Documents
    52. Policy Start Date
    53. Policy End Date


    Text:
    {text}
    """

# Schedule this function using Cron or similar tools
if __name__ == '__main__':
    # check_email()
    # ca_certs = certifi.where()
    query_chatgpt(generate_prompt("Dear Acko, I am writing to inform you about my recent accident. I was driving my car on the highway when a truck hit me from behind. I have attached the police report and photos of the accident. Please process my claim at the earliest."))