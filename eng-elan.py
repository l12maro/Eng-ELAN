import os
from re import findall
import re, sys
import aws, gcs

def add_transcriptions(file_, tier, output, transcriptions):
    # Which tier?
    tier_name = tier
    tree = ET.parse(file_[:-3] + "eaf")

    root = tree.getroot()

    #match transcription timestamps with tiers
    i = 1
    x = 0
    for times in root.iter('TIME_SLOT'):
        j = i + 1
        element = root.find('TIME_ORDER')
        e = element.findall('TIME_SLOT')
        s_time = ""
        e_time = ""
        for t in e:
            if t.get('TIME_SLOT_ID') == "ts" + str(i):
                s_time = t.get('TIME_VALUE')

            if t.get('TIME_SLOT_ID') == "ts" + str(j):
                e_time = t.get('TIME_VALUE')
                break
        list_of_items = transcriptions['results']['items']
        while True:
            if x >= len(list_of_items): break
            #convert time format and check where it belongs
            token = list_of_items[x]
            x += 1
            if token['type'] == "punctuation": continue
            token_start = token['start_time']
            token_start = int(float(token_start) * 1000)
            token_end = token['end_time']
            token_end = int(float(token_end) * 1000)
            
            if token_start >= int(s_time) and token_end <= int(e_time):
                #find the tier segment it belongs to
                for tier in root.iter('TIER'):
                    if tier.attrib['TIER_ID'] == tier_name:
                        for anon in tier.iter('ALIGNABLE_ANNOTATION'):
                            #for a in anon:
                            if anon.attrib['ANNOTATION_ID'] == "a" + str(int(j/2)):
                                for annotation in anon.iter('ANNOTATION_VALUE'):
                                    # insert text
                                    source_text = token["alternatives"][0]["content"]
                                
                                    # update the annotation
                                    if annotation.text == None:
                                        annotation.text = str(source_text)
                                    else:
                                        text = " " + str(source_text)
                                        annotation.text += text

                                    # feedback
                                    #print("done")

            
            #go to the next tier when all the words have been inserted
            else:
                if token_end > int(e_time): break
        i += 2

    # Save the file to output dir
    tree.write(os.path.join(path, os.path.basename(output)))

def main():
    # Read in all of the parameters that ELAN passes to this local recognizer on
    # standard input.
    params = {}
    for line in sys.stdin:
        match = re.search(r'<param name="(.*?)".*?>(.*?)</param>', line)
        if match:
            params[match.group(1)] = match.group(2).strip()
            print(params)

    #update wav file to the chosen service
    transcription = None
    if params['transcription_service'] == 'AWS':
        aws.upload_file(params["source"], params["bucket"], params["filename"])
        uri_path = "s3://" + params["bucket"] + "/" + params["filename"]
        #transcription now returns the json file with the transcription output
        transcription = aws.transcribe_file(params["filename"], uri_path, params["output_path"], params["bucket"])

    #Google Cloud is used as default service when the specified parameter is not AWS
    else:
        #update
        pass

    #now we add them to the eaf file within the chosen tier
    add_transcriptions(params['source'], params['tier'], params[''], transcription)

    # Finally, tell ELAN that we're done.
    print('RESULT: DONE.', flush=True)

if __name__ == "__main__":
    main()
