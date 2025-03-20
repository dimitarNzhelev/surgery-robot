import boto3

def upload_file_to_s3(file_path, bucket_name, s3_key):
    """
    Upload a file to an S3 bucket.
    
    Args:
        file_path (str): Local path of the file.
        bucket_name (str): Target S3 bucket name.
        s3_key (str): S3 object key (i.e., the destination path in the bucket).
    """
    s3_client = boto3.client('s3')
    s3_client.upload_file(file_path, bucket_name, s3_key)
