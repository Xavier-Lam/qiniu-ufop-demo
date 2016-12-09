#encoding: utf-8

import hashlib
import json
from flask import Flask, request, Response
import requests

app = Flask(__name__)

DEFAULTSIZE = 1024*256*256
DEFAULTALGORITHM = hashlib.md5
ALLOWEDALGORITHMS = dict(
    md5=hashlib.md5,
    sha1=hashlib.sha1,
    sha256=hashlib.sha256
)

@app.route("/uop", methods=["POST"])
def index():
    # 处理参数
    data = request.json
    url = data["src"]["url"]
    cmd = data["cmd"].split("/")
    fsize = data["src"]["fsize"]

    length = DEFAULTSIZE
    algorithm = DEFAULTALGORITHM
    if len(cmd) > 1:
        for o in cmd:
            if o in ALLOWEDALGORITHMS:
                algorithm = ALLOWEDALGORITHMS[o]
            elif o.isdigit():
                length = int(o)
    # 对于大于4M的MD5计算请求 只计算前4M
    if length > 4 * 1024 * 1024:
        length = 4 * 1024 * 1024
    if length > fsize:
        length = fsize

    # 请求文件 进行计算
    resp = requests.get(url, headers=dict(
        Range="bytes=0-" + str(length-1)
    ))
    digest = algorithm(resp.content).hexdigest()

    # 响应
    rv = Response()
    rv.headers["Content-Type"] = "application/json;charset=utf-8"
    rv.data = json.dumps(dict(
        digest=digest,
        algorithm=algorithm.__name__,
        fsize=fsize,
        mimetype=data["src"]["mimetype"],
        digestsize=length
    ))
    return rv

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9100)
