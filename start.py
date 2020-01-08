from __future__ import print_function
import time
import boto3
import botocore
from datetime import datetime
import shutil
import errno
import platform
import os
import transcript
import constant


def call_transcribe_api(jobname, speakers_number, bucket_name):
    transcribe = boto3.client('transcribe')
    job_uri = bucket_link

    transcribe.start_transcription_job(
        TranscriptionJobName=jobname,
        Media={'MediaFileUri': job_uri},
        MediaFormat='mp3',
        LanguageCode='en-US',
        OutputBucketName=bucket_name,
        Settings={
            "MaxSpeakerLabels": speakers_number,
            "ShowSpeakerLabels": True
        },
    )

    print("Processing Your File...")

    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=jobname)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        time.sleep(5)


def get_bucket_name():
    # Retrieve the list of existing buckets
    s3 = boto3.client('s3')
    response = s3.list_buckets()

    # get current bucket name
    for bucket in response['Buckets']:
        if bucket_link.find(bucket["Name"]) != -1:
            bucket_name = bucket["Name"]
            return bucket_name

    return ''


def download_transcribe_result(bucket_name, object_key, saved_file):
    s3 = boto3.resource('s3')

    try:
        s3.Bucket(bucket_name).download_file(object_key, saved_file)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise


def copy_json_file(src, dst):
    try:
        shutil.copy(src, dst)
    except OSError as e:
        if e.errno == errno.EEXIST:
            print('File not exist.')
        else:
            raise


if __name__ == '__main__':
    bucket_link = input("Enter Bucket Link: ")
    speakers_number = int(input("Number of Speakers: "))

    speakers = []
    i = 1
    while i <= speakers_number:
        speakers.append(input("Speaker %d Name: " % i))
        i += 1

    job_name = "Trans" + datetime.now().strftime("%Y%m%d%H%M%S")
    url_list = bucket_link.split("/")
    filename = url_list[len(url_list) - 1]

    split_bucket_link_by_dot = bucket_link.split(".")
    file_type = split_bucket_link_by_dot[len(split_bucket_link_by_dot) - 1]

    if file_type != "json":
        # New translation using api
        input_bucket = get_bucket_name()
        call_transcribe_api(job_name, speakers_number, input_bucket)

        key = job_name + '.json'
        json_dir = constant.DATA_STORAGE + '/' + filename + '/Original/JSON/'
        json_file = json_dir + filename + '.json'
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)

        html_dir = constant.DATA_STORAGE + '/' + filename + '/Original/HTML/'
        html_file = html_dir + filename + '.html'
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)

        download_transcribe_result(input_bucket, key, json_file)
        print("Transcription Complete!")
    else:
        # Using json file without api
        if platform.system() == 'Linux':
            split_bucket_link_by_slash = bucket_link.split('/')
        else:
            # Windows
            if bucket_link.find("https://") == -1:
                # local file
                split_bucket_link_by_slash = bucket_link.split('\\')
            else:
                # s3 bucket object
                split_bucket_link_by_slash = bucket_link.split('/')

        key = split_bucket_link_by_slash[len(split_bucket_link_by_slash) - 1]
        filename = key
        json_dir = constant.DATA_STORAGE + '/' + key + '/Original/JSON/'
        json_file = json_dir + key + '.json'
        if not os.path.exists(json_dir):
            os.makedirs(json_dir)

        html_dir = constant.DATA_STORAGE + '/' + key + '/Original/HTML/'
        html_file = html_dir + key + '.html'
        if not os.path.exists(html_dir):
            os.makedirs(html_dir)

        if bucket_link.find("https://") == -1:
            # if json file is stored in local
            copy_json_file(bucket_link, json_file)
        else:
            # if json file is stored in s3 bucket
            input_bucket = get_bucket_name()
            download_transcribe_result(input_bucket, key, json_file)

    sorted_data = transcript.parse_json(json_file, html_file, speakers)

    editable = input("Would you like to edit the transcription?")
    if editable.lower() == "yes" or editable.lower() == "y":
        transcript.convert_html(json_file, filename, sorted_data, speakers)
