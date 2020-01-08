import re


stirng = "https://sen-leach.s3.us-east-2.amazonaws.com/Jesse Eichenberg.mp3"
split_list = re.split(r"\[\d+\](.*?)\[\/\d+\]", stirng)
print(split_list)
print(len(split_list))
