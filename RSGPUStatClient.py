import os
import requests
import subprocess
import csv
import io
import json

POST_WEB = os.environ.get('POST_WEB') == '1'

WEB_API_ENDPOINT = os.environ.get('WEB_API_ENDPOINT')
WEB_API_TOKEN_ENDPOINT = os.environ.get('WEB_API_TOKEN_ENDPOINT')
if WEB_API_TOKEN_ENDPOINT is None or WEB_API_ENDPOINT is None:
    print('API URL not provided')
    POST_WEB = False

WEB_AUTH_USER = os.environ.get('WEB_AUTH_USER')
WEB_AUTH_PASSWORD = os.environ.get('WEB_AUTH_PASSWORD')

WEB_AUTH = ( WEB_AUTH_USER, WEB_AUTH_PASSWORD )

def run():
    # index, name, fan.speed [%], temperature.gpu, pstate, power.draw [W], power.limit [W], memory.used [MiB], memory.total [MiB], utilization.gpu [%], timestamp
    queries = 'index,name,fan.speed,temperature.gpu,pstate,power.draw,power.limit,memory.used,memory.total,utilization.gpu,timestamp'.split(',')
    cmd = 'nvidia-smi --query-gpu=%s --format=csv' % ','.join(queries)

    proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = proc.communicate()

    out = out.decode('utf-8')
    out = out.strip()

    out = io.StringIO(out)

    reader = csv.reader(out)
    next(reader)

    if POST_WEB:
        r = requests.get(WEB_API_TOKEN_ENDPOINT, auth=WEB_AUTH)
        js = r.json()
        token = js['token']

        gpus = []
        for row in reader:
            row = [ col.strip() for col in row ]
            gpu = {}
            for i in range(len(row)):
                gpu[queries[i]] = row[i]
            gpus.append(gpu)

        data = {
            'gpus': gpus,
        }
        data = json.dumps(data)

        pl = {
            'token': token,
            'data': data,
        }
        # print(pl)

        r = requests.post(WEB_API_ENDPOINT, auth=WEB_AUTH, data=pl, cookies=r.cookies)
        # print(r)
        # print(r.content)

if __name__ == '__main__':
    import schedule

    schedule.every(15).minutes.do(run)
