from google.cloud import speech
from google.cloud import storage


#TO DO: Add function to upload file
# The name of the audio file to transcribe

def upload_file(bucket, filename, destination, project):
    storage_client = storage.Client(project=project)
    bucket = storage_client.bucket(bucket)
    blob = bucket.blob(destination)

    blob.upload_from_filename(filename)

    print(
        f"File {filename} uploaded to {destination}."
    )


def transcribe_speech(uri):
    # Instantiates a client
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=uri)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code="en-US",
        enable_word_time_offsets=True,
    )

    # Detects speech in the audio file
    #response = client.recognize(config=config, audio=audio)
    operation = client.long_running_recognize(config=config, audio=audio)
    result = operation.result(timeout=90)

    return annotation_info(result)
      #for result in response.results:
        #print("Transcript: {}".format(result.alternatives[0].transcript))

def annotation_info(transcription):
    print(transcription)
    split_labels = []
    for result in transcription.results:
        alternative = result.alternatives[0]
        print("Transcript: {}".format(alternative.transcript))
        print("Confidence: {}".format(alternative.confidence))

        for word_info in alternative.words:
            start = int(float(word_info.start_time.total_seconds()) * 1000)
            end = int(float(word_info.end_time.total_seconds()) * 1000)
            content = word_info.word
            split_labels.append(dict( \
                [('start', start), \
                 ('end', end),
                 ("token", content)]))
        print(split_labels)
    #list_of_items = transcription['results']['items']
    #for items in list_of_items:
    #    if items['type'] == "punctuation": continue
    #    start = int(float(items['start_time']) * 1000)
    #    end = int(float(items['end_time']) * 1000)
    #    content = items["alternatives"][0]["content"]
    #    split_labels.append(dict( \
    #        [('start', start), \
    #         ('end', end),
    #         ("token", content)]))
    #print(split_labels)
    return split_labels
