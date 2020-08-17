# Automatic_summarization
Automatic Summary of multi speaker virtual meetings, podcasts, phone calls. 

## Overview
The Conversation Summarization API allows you to summarize the meaning of an audio transcript (speaker tagged), extracting its most relevant part of the conversation. The API provides two types of summaries:
Abstractive - Text summarization aims to understand the meaning behind a text and communicate it in newly generated sentences.


## Using

The Summarization API can be used in Python 3


### Requirements

pip3 install requests


### Python API

```bash
python3 deepaffects_summary_api.py --input_file_path=./sample/Podcast.txt --output_folder=./output --model=iamus
python3 deepaffects_summary_api.py -i ./sample/Podcast.txt -o ./output -m iamus
```





## About
DeepAffects is a speech analysis platform for Developers. We offer a number of speech analysis apis like, Speech Enhancement, Multi-Speaker Diarization, Emotion Recognition, Voice-prints, Conversation Metrics etc. For more information, checkout our [developer portal](https://developers.deepaffects.com)
