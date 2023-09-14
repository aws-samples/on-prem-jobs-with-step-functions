from awscrt import mqtt, http
from awsiot import mqtt_connection_builder
import sys
import os
import json
import threading


ENDPOINT=os.environ['ENDPOINT']
CA_FILE=os.environ['CA_FILE']
DEVICE_CERT=os.environ['DEVICE_CERT']
PRIVATE_KEY=os.environ['PRIVATE_KEY']
CLIENT_ID=os.environ['CLIENT_ID']
SUBSCRIBE_TOPIC=os.environ['SUBSCRIBE_TOPIC']
SUBMIT_TOPIC=os.environ['SUBMIT_TOPIC']


received_all_event = threading.Event()


# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print(
        "Connection resumed. return_code: {} session_present: {}".format(
            return_code, session_present
        )
    )

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results["topics"]:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print("Received message from topic '{}': {}".format(SUBMIT_TOPIC, payload))
    res = None
    taskToken = None
    try:
        inputBody = json.loads(payload)
        input = inputBody["Input"]
        taskToken = inputBody["TaskToken"]
        res = input["a"] + input["b"]
        print(res)

    except Exception as e:
        print(e)
        resp = {
            "result": res,
            "TaskToken": taskToken,
            "exception": type(e).__name__
        }
        message_json = json.dumps(resp)
        mqtt_connection.publish(
            topic=SUBMIT_TOPIC, payload=message_json, qos=qos
        )
        return
    
    try:
        print("Publishing messages to topic {}...".format(SUBMIT_TOPIC))
        resp = {
            "result": res,
            "TaskToken": taskToken
        }
        message_json = json.dumps(resp)
        print(message_json)
        mqtt_connection.publish(
            topic=SUBMIT_TOPIC, payload=message_json, qos=mqtt.QoS.AT_LEAST_ONCE
        )
    except Exception as e:
        print(e)
        resp = {
            "result": res,
            "TaskToken": taskToken,
            "exception": type(e).__name__
        }
        message_json = json.dumps(resp)
        mqtt_connection.publish(
            topic=SUBMIT_TOPIC, payload=message_json, qos=qos
        )


# Callback when the connection successfully connects
def on_connection_success(connection, callback_data):
    if isinstance(callback_data, mqtt.OnConnectionSuccessData):
        print(
            "Connection Successful with return code: {} session present: {}".format(
                callback_data.return_code, callback_data.session_present
            )
        )        


# Callback when a connection attempt fails
def on_connection_failure(connection, callback_data):
    if isinstance(callback_data, mqtt.OnConnectionFailuredata):
        print("Connection failed with error code: {}".format(callback_data.error))


# Callback when a connection has been disconnected or shutdown successfully
def on_connection_closed(connection, callback_data):
    print("Connection closed")


if __name__ == "__main__":
    # Create a MQTT connection from the command line data
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT,
        cert_filepath=DEVICE_CERT,
        pri_key_filepath=PRIVATE_KEY,
        ca_filepath=CA_FILE,
        client_id=CLIENT_ID,
        clean_session=False,
        keep_alive_secs=30,
        on_connection_success=on_connection_success,
        on_connection_failure=on_connection_failure,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        on_connection_closed=on_connection_closed
    )

    print(
        f"Connecting to {ENDPOINT} with client ID '{CLIENT_ID}'..."
    )
    connect_future = mqtt_connection.connect()

    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    subscribe_topic = SUBSCRIBE_TOPIC

    # Subscribe
    print("Subscribing to topic '{}'...".format(subscribe_topic))
    subscribe_future, packet_id = mqtt_connection.subscribe(
        topic=subscribe_topic, qos=mqtt.QoS.AT_LEAST_ONCE, callback=on_message_received
    )

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result["qos"])))

    # Wait for all messages to be received.
    # This waits forever if count was set to 0.
    if not received_all_event.is_set():
        print("Waiting for all messages to be received...")

    received_all_event.wait()

    # Disconnect
    print("Disconnecting...")
    disconnect_future = mqtt_connection.disconnect()
    disconnect_future.result()
    print("Disconnected!")
