# -*- coding:utf-8 -*-

import traceback
import base64
import hashlib
import hmac
import requests
import json
import wave
import sys
import subprocess
from datetime import datetime


class AliAsr(object):
    def __init__(self):
        self.access_key_id = "填你自己的key id"
        self.access_key_secret = '填你自己的key secret'
        # 是否使用opus格式
        self.is_opus = False

    @staticmethod
    def get_current_date():
        date = datetime.strftime(
            datetime.utcnow(), "%a, %d %b %Y %H:%M:%S GMT")
        return date

    @staticmethod
    def to_sha1_base64(string_to_sign, secretkey):
        hmacsha1 = hmac.new(secretkey, string_to_sign, hashlib.sha1).digest()
        return base64.b64encode(hmacsha1).decode('utf-8')

    def asr_buffer(self, file_buffer, rate):
        try:
            check_code = hashlib.md5(file_buffer).digest()
            check_code = hashlib.md5(base64.b64encode(check_code)).digest()
            check_code = base64.b64encode(check_code).decode("utf-8")

            date = self.get_current_date()
            if self.is_opus:
                sample = 'audio/opus; samplerate=16000'
            else:
                sample = 'audio/pcm; samplerate=16000'
            url = 'http://nlsapi.aliyun.com/recognize?model=customer-service'
            if rate == 8000:
                sample = 'audio/pcm; samplerate=8000'
                url = 'http://nlsapi.aliyun.com/recognize?model=customer-service-8k'
            feature = 'POST' + '\n' + 'application/json' + \
                      '\n' + check_code + '\n' + sample + '\n' + date

            feature = bytes(feature, 'latin-1')

            authorization_key = self.to_sha1_base64(feature, bytes(self.access_key_secret, 'latin-1'))

            headers = {
                'Content-type': sample,
                'Accept': 'application/json',
                'Authorization': 'Dataplus ' + self.access_key_id + ':' + authorization_key,
                'Date': date,
            }
            resp = requests.post(url, data=file_buffer, headers=headers)
            if 'SUCCEED' != json.loads(resp.text).get("status"):
                return ""
            else:
                return json.loads(resp.text).get("result")
        except Exception:
            print("ali recognize error: {}".format(traceback.format_exc()))
        return "error"

    def asr(self, wav_filepath):
        def get_wave_content(file_path):
            with wave.open(file_path, 'rb') as f:
                n = f.getnframes()
                sample_rate = f.getframerate()
                frames = f.readframes(n)
            return frames, sample_rate

        if self.is_opus:
            sample_rate = 16000
            frames = self.encode_opus(wav_filepath)
        else:
            frames, sample_rate = get_wave_content(wav_filepath)
        return self.asr_buffer(frames, sample_rate)

    @staticmethod
    def encode_opus(filename):
        args = ['opusenc', "--bitrate", "48", '--quiet', filename, '-']
        with open(filename, 'rb') as _:
            proc = subprocess.Popen(args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (out, err) = proc.communicate()
            if err or len(out) == 0:
                print('error', err)
            return out


if __name__ == '__main__':
    input_path = sys.argv[1]
    asr = AliAsr()
    start_time = datetime.now()
    result = asr.asr(input_path)
    end_time = datetime.now()
    use_time = end_time - start_time
    print(result)
    print(use_time.total_seconds() * 1000)
