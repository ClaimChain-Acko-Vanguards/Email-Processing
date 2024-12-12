import imaplib
import email
from email.header import decode_header
import os
from time import sleep

from PyPDF2 import PdfReader  # For reading PDFs
import pandas as pd  # For reading Excel files\
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance
import requests
from apscheduler.schedulers.background import BackgroundScheduler

# Variables

# Azure OpenAI endpoint and API key
url = "https://acko-01-ai.openai.azure.com/openai/deployments/gpt-4o/chat/completions"


def query_chatgpt(prompt):
    # Request headers
    headers = {
        "Content-Type": "application/json",
        "api-key": "api_key"
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
    Here is the list numbered:

    1. ledgerId  
    2. policyType  
    3. policyNumber  
    4. claimId  
    5. claimantName  
    6. phoneNumber  
    7. emailId  
    8. aadharId  
    9. insurerName  
    10. claimStatus  
    11. claimDate  
    12. claimAmount  
    13. settlementAmount  
    14. settlementDate  
    15. fraudScore  
    16. pincode  
    17. city  
    18. state  
    19. causeProof  
    20. causeStatement  
    21. thirdPartyInvolvement  
    22. errorCodes  
    23. claimProcessingTime  
    24. supportingDocuments  
    25. reasonForClaim  
    26. abhaId  
    27. hospitalName  
    28. diagnosisOrIllness  
    29. hospitalizationStartDate  
    30. hospitalizationEndDate  
    31. totalMedicalExpenses  
    32. preApprovedAmount  
    33. hospitalBills  
    34. testReports  
    35. initialAnalysis  
    36. finalAnalysis  
    37. iotDataAvailable  
    38. nomineeName  
    39. policyCoverage  
    40. vehicleRegistrationNo  
    41. vehicleType  
    42. vehicleMakeAndModel  
    43. carBikeAge  
    44. accidentDate  
    45. accidentLocation  
    46. garageName  
    47. repairEstimate  
    48. drivingBehaviorData  
    49. policyStartDate
    50. policyEndDate

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
                upload_claim(response)
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
                body += response
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
            full_text += page.extract_text()  # Extract typed text
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


def upload_claim(response):
    url = 'http://localhost:8080/claims/upload'
    headers = {
        'Content-Type': 'application/json',
        'Cookie': 'JSESSIONID=87FDF0E79EF0FE39C3B70B7E1C234D13'
    }

    payload = response
    print(payload)
    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            print("Claim uploaded successfully:", response.json())
        else:
            print("Failed to upload claim:", response.status_code, response.text)
    except requests.exceptions.RequestException as e:
        print("Error during the request:", e)


# Schedule this function using Cron or similar tools
if __name__ == '__main__':
    specific_sender = "rahultg741@gmail.com"  # Replace with the sender's email address
    while (True):
        check_email_from_specific_sender(specific_sender)
        sleep(1)
