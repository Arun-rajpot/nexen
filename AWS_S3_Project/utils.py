# utils.py
import logging
import psycopg2
import boto3
from botocore.exceptions import ClientError
import os
from urllib.parse import urlparse
import requests
import hashlib

LOG_FILE = r"E:\AWS_S3\Daily_Pdf_download_S3\script_log.txt"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_console_and_file(message, level="info"):
    print(message)
    if level == "error":
        logging.error(message)
    else:
        logging.info(message)

def get_database_connection():
    try:
        return psycopg2.connect(
            dbname="company_uat",
            user="postgres",
            password="postgres",
            port="5432"
        )
    except psycopg2.Error as e:
        log_console_and_file(f"Error: Unable to connect to the database - {e}", "error")
        return None






def get_s3_client():
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=S3_REGION
        )


        return s3_client
    except Exception as e:
        print(f"❌ Failed to create S3 client: {e}")
        return None


# def download_file_directly():
#     s3 = get_s3_client()
#     object_key = "https://nexensus-docs-bucket.s3.ap-south-1.amazonaws.com/Jboss.txt"  # Replace this with known key
#     local_file = "file.pdf"
#
#     try:
#         s3.download_file(S3_BUCKET_NAME, object_key, local_file)
#         print(f"Downloaded: {local_file}")
#     except Exception as e:
#         print("Error downloading file:", e)
#
# download_file_directly()


def s3_file_exists(bucket, key):
    #print("key===",key)
    try:
        get_s3_client().head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == "404":
            return False
        elif error_code == "403":
            print(f"❌ Access denied (403) to check object: {key}")
            return None  # Or handle as you want
        else:
            raise
#
#======= file save in s3 ==============================

def upload_to_s3_if_not_exists(content: bytes, s3_key: str, content_type="application/pdf"):

    s3 = get_s3_client()

    #print(s3)
    if not s3:
        print("❌ Could not create S3 client.")
        return False

    exists = s3_file_exists(S3_BUCKET_NAME, s3_key)
    if exists is True:
        log_console_and_file(f"[Skip] Already exists in S3: s3://{S3_BUCKET_NAME}/{s3_key}")
        return False
    elif exists is None:
        log_console_and_file(f"[Error] Access denied checking if file exists: s3://{S3_BUCKET_NAME}/{s3_key}")
        return False

    try:
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=content,
            ContentType=content_type,
            StorageClass='GLACIER_IR'
        )
        
        log_console_and_file(f"[Uploaded] s3://{S3_BUCKET_NAME}/{s3_key}")
        return True
    except Exception as e:
        log_console_and_file(f"[Error] Failed to upload {s3_key} to S3: {str(e)}")
        return False

# ====== file  save in local =======================================


def is_file_exists_locally(local_path):
    """
    Check if a file already exists locally.
    :param local_path: Full local file path
    :return: True if file exists, False otherwise
    """
    try:
        if os.path.exists(local_path):
            print(f"File already exists locally: {local_path}")
            return True
        return False
    except Exception as e:
        print(f"Error checking local file existence: {e}")
        return False


def save_to_local_if_not_exists(content, local_path):
    """
    Save file locally if it does not already exist.
    :param content: File content (bytes)
    :param local_path: Full local file path
    """
    try:
        # Skip if file already exists
        if is_file_exists_locally(local_path):
            return False

        # Ensure directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Save file
        with open(local_path, "wb") as f:
            f.write(content)
        print(f"File saved locally: {local_path}")
        return True
    except Exception as e:
        print(f"Error saving file locally: {e}")
        return False



def generate_safe_filename_from_url(url: str, add_extension: str = None) -> str:
    """
    Generate a safe filename from URL using SHA256 hashing.
    Returns 64-char SHA256 hex string + optional extension.
    """
    # SHA256 hash of URL
    sha256_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()  # always 64 chars

    # Add extension if provided
    if add_extension:
        add_extension = add_extension.lower()
        if not add_extension.startswith("."):
            add_extension = "." + add_extension
        if not sha256_hash.lower().endswith(add_extension):
            sha256_hash = sha256_hash + add_extension

    return sha256_hash


# ====== download file from bucket ===============================

# def download_from_s3(bucket_name, object_key, download_path):
#
#     s3 = get_s3_client()
#
#     try:
#         s3.download_file(bucket_name, object_key, download_path)
#         print(f"✅ Downloaded: s3://{bucket_name}/{object_key} → {download_path}")
#         return True
#     except ClientError as e:
#         print(f"❌ Failed to download file: {e}")
#         return False
#
# download_from_s3(
#     bucket_name='nexensus-docs-bucket',
#     object_key='Test_Document_download/L34300HR2005PLC081531/ratings/2018-12-17_CRISIL.pdf',
#     download_path='D:\\CRISIL_2018-12-17.pdf'
#
# )


# ==== get list of object =======


# def test_():
#     s3 = get_s3_client()
#     response = s3.list_objects_v2(Bucket='nexensus-docs-bucket')
#     print(response)
#
# test_()


