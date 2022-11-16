from google.cloud import speech
from google.cloud import storage

# Instantiates a client
client = speech.SpeechClient()

#TO DO: Add function to upload file
# The name of the audio file to transcribe

def upload_file(bucket, filename, destination):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket)
    blob = bucket.blob(destination)

    blob.upload_from_filename(filename)

    print(
        f"File {filename} uploaded to {destination}."
    )

def transcribe_speech(uri):
  audio = speech.RecognitionAudio(uri=uri)

  config = speech.RecognitionConfig(
      encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
      sample_rate_hertz=44100,
      language_code="en-US",
  )

  # Detects speech in the audio file
  response = client.recognize(config=config, audio=audio)

  return response.results
  #for result in response.results:
    #print("Transcript: {}".format(result.alternatives[0].transcript))

