import pika, json

def upload(f, fs, channel, access):
    try:
        # Upload file to server
        fid = fs.put(f)
    except Exception as err:
        print("Error uploading file", err)
        return "Internal server error fs level", 500

    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }

    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        print("Error uploading message", err)
        fs.delete(fid)
        return f"Internal server error rabbitmq issue, {err}", 500