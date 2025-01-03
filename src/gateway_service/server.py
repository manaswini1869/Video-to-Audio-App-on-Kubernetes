import os, gridfs, pika, json
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId
from werkzeug.middleware.dispatcher import DispatcherMiddleware

server = Flask(__name__)

mongo_video = PyMongo(server, uri=os.environ.get('MONGO_VIDEOS_URI'))

mongo_mp3 = PyMongo(server, uri=os.environ.get('MONGODB_MP3S_URI'))

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq", heartbeat=0))
channel = connection.channel()

@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if not err:
        return token, 200
    else:
        return err, 400

@server.route("/upload", methods=["POST"])
def upload():
    access, err = validate.token(request)

    if err:
        unauth_count.inc()
        return err

    access = json.load(access)

    if access["admin"]:
        if len(request.files) > 1 or len(request.files < 1):
            return "Requires file count exactly 1", 400
        for _, f in request.files.items():
            err = util.upload(f, fs_videos, channel, access)

            if err:
                return err, 400

        return "Success", 200
    else:
        return "Not Authorized", 401

@server.route("/download", method=["GET"])
def download():
    access, err = validate.token(request)

    if err:
        unauth_count.inc()
        return err

    access = json.loads(access)

    if access["admin"]:
        fid_string = request.args.get("fid")

        if not fid_string:
            return "Fid is required", 400

        try:
            out = fs_mp3s.get(ObjectId(fid_string))
            return send_file(out, download_name=f"{fid_string}.mp3")
        except Exception as err:
            print(err)
            return "Internal server error", 500

    return "Not Authorized", 401

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)

