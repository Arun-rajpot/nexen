import os
import shutil
import boto3
import traceback
from botocore.exceptions import ClientError
import time
from datetime import datetime

daily_total_cin = 0
daily_transferred_cin = 0
daily_s3_cin = 0

def count_cin_directories(path):
    try:
        cin_count = 0

        for item in os.listdir(path):
            full_path = os.path.join(path, item)

            if os.path.isdir(full_path):
                if item not in [".stfolder", ".stversions"]:
                    cin_count += 1

        return cin_count

    except Exception as e:
        log_exception(e, context="count_cin_directories")
        return 0

def write_cin_summary(daily_total_cin):
    global  daily_transferred_cin, daily_s3_cin

    today = datetime.now().strftime("%Y-%m-%d")

    

    summary_file = "daily_cin_transfer_summary.txt"

    summary = (
        f"{today} :\n"
        f"Total CIN Received : {daily_total_cin}\n"
        f"Successfully Transferred to 55 Server : {daily_transferred_cin}\n"
        f"Successfully Uploaded to S3 : {daily_s3_cin}\n"
        "-----------------------------------------\n"
    )

    with open(summary_file, "a") as f:
        f.write(summary)

    print("\n📊 DAILY CIN SUMMARY")
    print(summary)

# ========== CONFIG ==========
bucket_name = "nexensus-docs-bucket"  # Only bucket name
s3_root_prefix = "documents"  # Folder inside bucket, no leading slash


#s3_bucket = "s3://nexensus-docs-bucket/documents/"
error_log_path = r"D:\Aws_project\55_Code\s3_upload_errors.log"
success_log_path = r"D:\Aws_project\55_Code\s3_upload_success.log"



AWS_ACCESS_KEY = "your AWS_ACCESS_KEY"
AWS_SECRET_KEY = "your AWS_SECRET_KEY"
#S3_BUCKET_NAME = "your"
S3_REGION = "your"

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




# ========== LOGGING ==========
def log_success(msg):
    with open(success_log_path, "a") as lf:
        lf.write(msg + "\n")

def log_error(msg):
    with open(error_log_path, "a") as lf:
        lf.write(msg + "\n")

def log_exception(e, context=""):
    with open(error_log_path, "a") as lf:
        lf.write("\n========== EXCEPTION ==========\n")
        if context:
            lf.write(f"Context: {context}\n")
        lf.write(str(e) + "\n")
        lf.write(traceback.format_exc() + "\n")

# ========== SAFE DELETE ==========
def safe_delete(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        print(f"🗑 Deleted from source: {path}")
        log_success(f"Deleted from source: {path}")
    except Exception as e:
        log_exception(e, context=f"safe_delete path={path}")

def remove_cin_dirs(path):
    print("hii.....")
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
            log_success(f"[REMOVED DIR] {path}")
            print(f"🗑 Removed directory: {path}")
        else:
            print(f"⚠ Path not found: {path}")
    except Exception as e:
        log_exception(e, context=f"remove_empty_dirs failed on {path}")
        
        
# ========== S3 UPLOAD FUNCTIONS ==========
def upload_file_to_s3(local_file, bucket, key):
    #s3_client = get_s3_client()
    try:
        #s3_client.upload_file(
        #    local_file,
        #    bucket,
         #   key,
          #  ExtraArgs={"StorageClass": "GLACIER_IR"}
        #)
        print(f"✔ Uploaded: {key}")
        log_success(f"Uploaded: {key}")

    except Exception as e:
        print(f"❌ Upload failed: {key}")
        log_exception(e, context=f"upload_file_to_s3 key={key}")

# ========== S3 UPLOAD ==========
def upload_folder_to_s3(local_path, bucket, prefix):
    try:
        #s3_client = get_s3_client()
        for root, dirs, files in os.walk(local_path):
            for file in files:
                local_file = os.path.join(root, file)
                rel_path = os.path.relpath(local_file, local_path)
                s3_key = f"{prefix}/{rel_path}".replace("\\", "/")
                #s3_client.upload_file(local_file, bucket, s3_key)
                log_success(f"Uploaded: {s3_key}")
    except Exception as e:
        log_exception(e, context=f"upload_folder_to_s3 path={local_path}")

# ========== LOCAL COPY ==========
def copy_folder_filewise(src, dst):
    try:
        for root, dirs, files in os.walk(src):
            rel_path = os.path.relpath(root, src)
            dest_folder = dst if rel_path == "." else os.path.join(dst, rel_path)
            os.makedirs(dest_folder, exist_ok=True)

            for file in files:
                shutil.copy2(os.path.join(root, file), os.path.join(dest_folder, file))
    except Exception as e:
        log_exception(e, context=f"copy_folder_filewise src={src}")

# ========== COMPARE ==========
def compare_folders(cin, folder1, folder2, file, copy_missing, base_cin_folder, indent=0):
    try:
        prefix = " " * indent

        folder1_items = set(os.listdir(folder1))
        folder2_items = set(os.listdir(folder2))

        missing_items = folder1_items - folder2_items
        common_items = folder1_items & folder2_items

        for item in sorted(missing_items):
            src = os.path.join(folder1, item)
            dst = os.path.join(folder2, item)
            
            
            if copy_missing:
                try:
                    with open("script_log_comparision_missing_file.txt", 'a') as f:
                            f.write(f"{cin}{prefix}[NEW] {src}\n")
                        # print(f"{prefix}[NEW] {item}")
                    rel_path = os.path.relpath(src, base_cin_folder)
                    s3_prefix = f"{s3_root_prefix}/{cin}/{rel_path.replace(os.sep, '/')}"
                    print(s3_prefix)
                    if os.path.isdir(src):
                        os.makedirs(dst, exist_ok=True)
                        copy_folder_filewise(src, dst)
                        upload_folder_to_s3(src, bucket_name, s3_prefix)
                    else:
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
                        
                        #  Fix S3 root-level issue
                        if rel_path == ".":
                            s3_key = f"{s3_root_prefix}/{cin}/{item}"
                            
                        else:
                            s3_key = f"{s3_root_prefix}/{cin}/{rel_path.replace(os.sep, '/')}"
                            
                        upload_file_to_s3(src, bucket_name, s3_key)

                    safe_delete(src)
                except Exception as e:
                    log_exception(e, context=f"copying {src}")

        for item in common_items:
            path1 = os.path.join(folder1, item)
            path2 = os.path.join(folder2, item)
            if os.path.isdir(path1) and os.path.isdir(path2):
                compare_folders(cin, path1, path2, file, copy_missing, base_cin_folder, indent + 4)

    except Exception as e:
        log_exception(e, context=f"compare_folders cin={cin}")

# ========== BASE ==========
def compare_base_folders(source, dest, output_dir, folder_name, copy_flag):
    try:
        out_file = os.path.join(output_dir, f"{folder_name}_comparison.txt")

        with open(out_file, "w") as f:
            for cin in os.listdir(source):
                
                global daily_transferred_cin, daily_s3_cin
                
                log_success(cin)
                print(cin)
                if cin == ".stfolder" or cin == ".stversions":
                    continue
                src = os.path.join(source, cin)
                dst = os.path.join(dest, cin)

                if not os.path.isdir(src)  :
                    continue

                os.makedirs(dst, exist_ok=True)
                compare_folders(cin, src, dst, f, copy_flag, base_cin_folder=src, indent=2)
                
                daily_transferred_cin += 1
                daily_s3_cin += 1
                
                print(src)
                remove_cin_dirs(src)
                

    except Exception as e:
        log_exception(e, context="compare_base_folders")

# ========== RUN ==========

def main():
    global daily_total_cin,daily_transferred_cin, daily_s3_cin
    
    base_dir_1 = r"D:\Aws_project\55_Code\New_files"
    base_dir_2 = r"D:\Aws_project\55_Code\Old_files"
    output_file = r"D:\Aws_project\55_Code"
      

    daily_total_cin = count_cin_directories(base_dir_1)
    compare_base_folders(base_dir_1, base_dir_2, output_file, "script_log", True)
    
    
    write_cin_summary(daily_total_cin)
        
    print("✅ DONE")

# ========== SCHEDULER ==========
def run_scheduler():
    print("🕒 Scheduler started (checking every 60 seconds)...")
    while True:
        try:
            global daily_total_cin, daily_transferred_cin, daily_s3_cin

            daily_total_cin = 0
            daily_transferred_cin = 0
            daily_s3_cin = 0
            
            main()
        except Exception as e:
            log_exception(e, "scheduler")
        time.sleep(60)

# ========== START ==========
if __name__ == "__main__":
    run_scheduler()