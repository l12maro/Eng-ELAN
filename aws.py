import time, json
import boto3

transcribe_client = boto3.client('transcribe')
s3 = boto3.client('s3')

def upload_file(filename, bucket, key):
    s3.upload_file(filename, bucket, key)

def transcribe_file(job_name, file_uri, bucket, output_url):
    print(file_uri)
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        MediaFormat='wav',
        LanguageCode='en-US',
        OutputBucketName=bucket
    )

    max_tries = 60
    while max_tries > 0:
        max_tries -= 1
        job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        job_status = job['TranscriptionJob']['TranscriptionJobStatus']
        if job_status in ['COMPLETED', 'FAILED']:
            print(f"Job {job_name} is {job_status}.")
            if job_status == 'COMPLETED':
                #download json file and access it
                s3.download_file(bucket, job_name + ".json", output_url + job_name + ".json")
                transcriptionfile = json.load(open(output_url + job_name + ".json"))
                return annotation_info(transcriptionfile)
            break
        else:
            print(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(10)

#returns the transcription information as a list of dictionaries
def annotation_info(transcription):
    split_labels = []
    list_of_items = transcription['results']['items']
    for items in list_of_items:
        if items['type'] == "punctuation": continue
        start = int(float(items['start_time']) * 1000)
        end = int(float(items['end_time']) * 1000)
        content = items["alternatives"][0]["content"]
        split_labels.append(dict( \
            [('start', start), \
             ('end', end),
             ("token", content)]))
    return split_labels
