import imaplib
import email
from email.header import decode_header
import os
from PyPDF2 import PdfReader  # For reading PDFs
import pandas as pd          # For reading Excel files\
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance
import requests
from apscheduler.schedulers.background import BackgroundScheduler

# Variables

# Azure OpenAI endpoint and API key
url = "https://acko-01-ai.openai.azure.com/openai/deployments/gpt-4o/chat/completions"
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


# Generate a prompt for extracting fields
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

def decode_header_value(header_value):
    """Decodes email header values to handle special characters."""
    decoded_parts = decode_header(header_value)
    header_parts = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            header_parts.append(part.decode(encoding or 'utf-8'))
        else:
            header_parts.append(part)
    return ''.join(header_parts)


def check_email_from_specific_sender(sender_email):
    """Checks unread emails from a specific sender."""
    # Connect to IMAP server
    server = 'imap.gmail.com'
    username = 'xyz69641@gmail.com'
    password = 'yxhm uuly payy rugr'

    mail = imaplib.IMAP4_SSL(server)
    mail.login(username, password)

    text = ''

    try:
        # Select inbox
        mail.select("inbox")

        # Search for unread emails from the specific sender
        search_criteria = f'UNSEEN FROM "{sender_email}"'
        status, messages = mail.search(None, search_criteria)

        if messages[0]:  # Check if any emails match the search
            for num in messages[0].split():
                status, data = mail.fetch(num, '(RFC822)')
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Extract email details
                subject = decode_header_value(msg["Subject"])
                sender = decode_header_value(msg.get("From"))
                print(f"New email from: {sender}")
                print(f"Subject: {subject}")

                # Process the email (extract body and attachments)
                text = process_email(msg)
                prompt = generate_prompt(text)
                response = query_chatgpt(prompt)
                print(response)

        else:
            print(f"No unread emails found from {sender_email}.")
    except imaplib.IMAP4.abort as e:
        print(f"IMAP connection aborted: {e}")
    finally:
        try:
            mail.close()
        except imaplib.IMAP4.abort as e:
            print(f"Error closing mailbox: {e}")
        mail.logout()


def process_email(msg):
    """Processes the email to extract body and attachments."""
    body = None
    for part in msg.walk():
        if part.get_content_type() == "text/plain" and not part.get_content_disposition():
            # Decode the plain text email body
            body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
            # Print the email body
            if body:
                print(f"Body:\n{body}")
        elif part.get_content_disposition() == "attachment":
            # Save attachments
            filename = decode_header_value(part.get_filename())
            if filename:
                filepath = os.path.join("./documents", filename)
                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))
                print(f"Attachment saved: {filepath}")

                response = ''
                # Process the attachment based on its file type
                if filename.endswith(".pdf"):
                    response = read_pdf(filepath)
                elif filename.endswith(".txt"):
                    response = read_txt(filepath)
                elif filename.endswith(".xlsx") or filename.endswith(".xls"):
                    response = read_excel(filepath)
                body+=response
    return body


def read_pdf(filepath):
    """Reads and prints content from a PDF file."""
    try:
        reader = PdfReader(filepath)
        print(f"\n--- Content of PDF {filepath} ---")
        data = ''
        for page in reader.pages:
            print(page.extract_text())
            data += page.extract_text()
        return data
    except Exception as e:
        print(f"Error reading PDF {filepath}: {e}")


def read_txt(filepath):
    """Reads and prints content from a TXT file."""
    try:
        data = ''
        with open(filepath, "r", encoding="utf-8") as file:
            print(f"\n--- Content of TXT {filepath} ---")
            print(file.read())
            data += file.read()
        return data
    except Exception as e:
        print(f"Error reading TXT {filepath}: {e}")


def read_excel(filepath):
    """Reads and prints content from an Excel file."""
    try:
        print(f"\n--- Content of Excel {filepath} ---")
        df = pd.read_excel(filepath)  # Reads the Excel file into a DataFrame
        print(df.to_string(index=False))  # Prints the DataFrame
        return df.to_string(index=False)
    except Exception as e:
        print(f"Error reading Excel {filepath}: {e}")





def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() # Extract typed text
    print(full_text)
    return full_text


def preprocess_image(image):
    # Convert image to grayscale
    gray_image = image.convert("L")

    # Apply thresholding to make text stand out more
    threshold_image = gray_image.point(lambda p: p > 180 and 255)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(threshold_image)
    enhanced_image = enhancer.enhance(2.0)

    return enhanced_image


def ocr_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""

    for image in images:
        # Preprocess the image for better OCR results
        preprocessed_image = preprocess_image(image)

        # Use Tesseract to extract text from the image
        text += pytesseract.image_to_string(preprocessed_image)
    print(text)
    return text


def process_pdf(pdf_path):
    # Extract typed text
    typed_text = extract_text_from_pdf(pdf_path)

    # Extract handwritten text
    handwritten_text = ocr_from_pdf(pdf_path)

    # Combine both typed and handwritten text
    full_text = typed_text + "\n" + handwritten_text
    return full_text



def job():
    specific_sender = "rahultg741@gmail.com"  # Replace with the sender's email address
    check_email_from_specific_sender(specific_sender)


# Schedule this function using Cron or similar tools
if __name__ == '__main__':
    # specific_sender = "rahultg741@gmail.com"  # Replace with the sender's email address
    # check_email_from_specific_sender(specific_sender)

    data = '''
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
    Dear Go Digit Insurance,

Please find below the details of the health claim submitted for processing
under the policy.

Insurer Name: Go Digit Insurance Co.

Claimant Details:

Name: Mr. Rahul Sharma
Age: 42
Policy Number: XYZ12345678
Sum Insured: ₹10,00,000

Hospitalization Details:

Start Date: 01 December 2024
End Date: 05 December 2024
Hospital Name: City Care Hospital, Mumbai
Claim Details:

Total Medical Expenses (₹): ₹2,50,000
Pre-Approved Amount (₹): ₹1,50,000
Policy Coverage (₹): ₹10,00,000
Supporting Documents:

Hospital Bills (Attached)
Test Reports (Attached)
Cause Proof: Medical Certificate from attending physician (Attached)
Reason for Claim: Treatment for acute appendicitis requiring laparoscopic
surgery.

Cause Statement: The patient experienced severe abdominal pain and was
diagnosed with acute appendicitis following a CT scan. Surgery was
performed to prevent complications.

Third-Party Involvement: None

Error Codes: N/A

Claim Processing Time: Standard processing timeline of 15 business days
applies.

Additional Information:

Nominee Name: Mrs. Priya Sharma
Initial Analysis: The submitted documents and medical reports confirm the
treatment's necessity and validity under the policy terms.
Final Analysis: Awaiting further verification from your team to finalize
the claim amount.
Please let us know if any additional documents or clarifications are
required to expedite the claim processing.




Regards,
Rahul T G
Manager, Ops
FHPL

    '''
    response = query_chatgpt(data)

    # prompt = generate_prompt(text)
    # response = query_chatgpt(prompt)
    #
    #
    # # Example usage
    # pdf_path = "documents/Endorsement-Schedule-GMC123456107.pdf"
    # text = process_pdf(pdf_path)

    scheduler = BackgroundScheduler()

    scheduler.add_job(job, 'interval', minutes=1)
    scheduler.start()

    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()