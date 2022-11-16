# Eng-ELAN 0.1
Eng-ELAN integrates the Text-to-Speech services offered by Amazon Web Services and Google Cloud to ELAN. It allows users to apply automatic transcription to English audio from ELAN's interface.

## Requirements and installation
In order to use Eng-ELAN, the following open-source applications are required:
* ELAN (tested with ELAN 6.4 under Windows 10)
* Python 3 (tested with Python 3.9)

The following command can be used to fetch the recognizer:
```
git clone -b ELAN https://github.com/l12maro/ASR_English
cd ASR-English

python3 -m virtualenv venv-eng
source venv-eng/bin/activate
```
The following Python packages are required and should be installed in the virtual environment:
* For Google Cloud Transcription Services, the following modules:
  * [Storage](https://pypi.org/project/google-cloud-speech/)
  * [Speech](https://pypi.org/project/google-cloud-storage/)
* For Amazon Web Services:
  *  [boto3](https://pypi.org/project/boto3/) 

Additionally, to use this recognizer it is necessary to have an existing account in the Text-to-Speech service that you wish to use, and have access from the Power Shell.
In the Text-to-Speech service, you need to previously create:
* A project (only for Google Cloud)
* A bucket or storage where the sound files to transcribe will be uploaded

To make Eng-ELAN available under ELAN recognizers, the following changes are required:
* For Windows, edit the file ` eng-elan.bat ` with the path to your python environment
* Move your Eng-ELAN directory into ELAN's ` extensions ` directory
* Restart ELAN to see the recognizer

To use the user interface of this recognizer, you need to provide the following information:
* *URL to Google Cloud Project:* Provide the link to your Google Cloud project. Skip this step if using Amazon Web Services. This link will have the following format: 
` https://storage.googleapis.com/storage/v1/b?project={PROJECT NAME} `
* *Bucket name:* The name of your bucket where you will store the sound file, in either Amazon Web Services or Google Cloud.
* *Filename:* A name you choose for the file you will upload, as well as for the transcription job. If using Amazon Web Services, this must be a unique name that has not been previously used.
* *Output:* The path to an existing xml file where your tier will be stored. 
