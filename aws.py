import time, json
import boto3

transcribe_client = boto3.client('transcribe')
s3 = boto3.client('s3')

def upload_file(filename, bucket, key):
    s3.upload_file(filename, bucket, key)

def transcribe_file(job_name, file_uri, output_uri, output_url):
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        MediaFormat='wav',
        LanguageCode='en-US',
        OutputBucketName=output_uri
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
                s3.download_file(output_uri, job_name + ".json", output_url + job_name + ".json")
                return json.load(open(output_url + job_name + ".json"))
                #print("Transcription: " + transcription['results']['transcripts'][0]['transcript'])

            break
        else:
            print(f"Waiting for {job_name}. Current status is {job_status}.")
        time.sleep(10)


#def main():
    #transcribe_client = boto3.client('transcribe')
    #s3 = boto3.client('s3')
    #transcribe_file('prueba', file_uri, output_uri, output_url, transcribe_client, s3)


#if __name__ == '__main__':
#    main()