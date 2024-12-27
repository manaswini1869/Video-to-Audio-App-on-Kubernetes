import pika, sys, os
from send import email

def main():
    # Create a connection to the RabbitMQ server
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', heartbeat=0))
    channel = connection.channel()

    def callback(ch, method, properties, body):
        err = email.notification(body)
        if err:
            print(f"Error sending email: {err}")
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("MP3_QUEUE"), on_message_callback=callback
    )

    print("Waiting for messages. To exit press CTRL+C")

    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted, stopping ..")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)