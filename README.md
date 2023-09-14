# Run jobs on-premises with AWS Step Functions and MQTT

This project demostrates how AWS Step Functions can dispatch jobs to on-premises systems without requiring inbound Internet connectivity or public endpoints. The pattern relies on [MQTT protocol](https://docs.aws.amazon.com/iot/latest/developerguide/mqtt.html) to dispatch jobs and on a [Callback with the Task Token](https://docs.aws.amazon.com/step-functions/latest/dg/connect-to-resource.html#connect-wait-token) from AWS Step Functions.

![Diagram](readme_assets/diagram.svg)

### Diagram Workflow
1. State machine is triggered on-demand or on schedule. 
1. Lambda `Dispatch Job to On-Premises` state publishes a message to an MQTT Message Broker.
1. Message broker sends the message to the topic, corresponding to the tenant.
1. On-premise container listens for new messages, starts work execution when notified from the cloud. It authenticates through certificates and is limited to only its tenant's topic by the attached policy.
1. On-premise container has access to an internal on-premise resources like DBs or SAP instances (DBs and local storage is out of scope of this sample repository).
1. On-premise container sends the results and status back to another topic.
1. IoT Core Rule triggers Lambda Function.
1. The Lambda Function submits the results to Step Functions via SendTaskSuccess or SendTaskFailure API.

## Project structure

This project contains resources provisioned to AWS, including AWS Lambda functions and Step Functions State Machine. These resources are located in `aws-resources` directory and can be deployed with `template.yml` – an AWS Serverless Application Model (SAM) template file.

The directory `on-prem-worker` contains a worker, which can be deployed outside of AWS, for example in on-premises datacenter with no inbound ports open nor public endpoints exposed.

## Requirements

* [Create AWS Account](https://portal.aws.amazon.com/gp/aws/developer/registration/index.html) in case you do not have it yet or log in to an existing one
* An IAM user or a Role with sufficient permissions to deploy and manage AWS resources
* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) installed and configured
* [Git Installed](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
* [AWS Serverless Application Model](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) (AWS SAM) installed
* [Python](https://www.python.org/downloads/) for changing AWS Lambda functions' code
* [Docker](https://docs.docker.com/engine/install/) for running a mock on-premises worker installed

## Deployment instructions

The project contains AWS resources and Docker container definition to run on-premises.

### AWS Resources

1. Open a terminal and create a new directory, which you will use to clone the repository from GitHub.
1. Clone GitHub repository:
    ``` bash
    git clone https://github.com/aws-samples/on-prem-jobs-with-step-functions.git
    ```
1. Change directory to the cloned repository:
    ``` bash
    cd on-prem-jobs-with-step-functions
    ```
1. Go to `aws-resources` directory
    ``` bash
    cd aws-resources
    ```
1. Make sure that your terminal can access AWS resources. Use AWS SAM to deploy the backend resources:
    ``` bash
    sam build && sam deploy --guided
    ```
1. When prompted:
    * Specify a stack name
    * Choose AWS Region
    * Allow SAM CLI to create IAM roles with the required permissions.

    You can use the template defaults for other parameters.
    
    Once you have finished the setup, SAM CLI will save the specified settings in configuration file samconfig.toml so you can use `sam deploy` for quicker deployments.

At this point, you have almost all the resources provisioned in AWS. You only need to create certificates for the IoT Core Thing and link them to the policy. Follow these steps:

1. In your browser, navigate to [IoT Core Things](https://console.aws.amazon.com/iot/home#/thinghub). Make sure you are in the right region and you can see your provisioned Thing in the list (default name is `mqtt-container-client`).
1. Press on `mqtt-container-client` and select `Certificates` tab.
1. Press `Create certificate` button.
1. In the `Download certificates and keys` modal dialog, activate the `Device certificate` by pressing `Activate certificate` button. Download `Device certificate`, `Key files`, and `RSA 2048 bit key: Amazon Root CA 1`.
1. Press `Done` button.
1. Press on the name of the newly created certificate.
1. Press on `Attach policies` button and select `OnPremContainer`.
1. Press `Attach policies` to accept and close the modal dialog.

Now your AWS configuration is complete. Move to the next section to create an on-premises container.

### On-premises Container

1. Navigate to `on-prem-worker`:
    ``` bash
    cd ../on-prem-worker
    ```
1. Run this command to determine Amazon Trust Services (ATS) endpoint from IoT Core. Substitute `<YOUR_REGION>` placeholder with the region you have deployed your AWS resources to:
    ``` bash
    aws iot describe-endpoint --endpoint-type iot:Data-ATS --region <YOUR_REGION> | jq -r .endpointAddress
    ```
    Your output should look like:
    ```
    abc123defghijk-ats.iot.<YOUR_REGION>.amazonaws.com
    ```
    Make a note of the endpoint.
1. Open `Dockerfile` and on the line 3 replace the placeholder `<IOT_CORE_ENDPOINT_URL>` with the value from the previous step. Save the file.
1. Go to `on-prem-worker/certs` directory and copy the contents of the certificates you downloaded in the previous section. `cert.pem` – device certificate, `priv.key` – private key, `root-CA.crt` – Amazon Root CA 1.
1. Build docker container:
    ``` bash
    docker build . -t mqtt-client-waitfortoken
    ```
1. Wait for the build to finish and check if the container image exists:
    ``` bash
    docker images
    ```
    You should see your new image in the output:
    ```
    mqtt-client-waitfortoken
    ```
1. Run docker container:
    ``` bash
    docker run -it mqtt-client-waitfortoken
    ```
    Your output should look similar to this:
    ```
    Connecting to abc123defghijk-ats.iot.<YOUR_REGION>.amazonaws.com with client ID 'mqtt-container-client'...
    Connection Successful with return code: 0 session present: False
    Connected!
    Subscribing to topic 'tenant1/to/worker'...
    Subscribed with QoS.AT_LEAST_ONCE
    Waiting for all messages to be received...
    ```
    Your on-prem container is now ready and is listening for incoming messages.

    If you need to stop the container, use `CMD+C` keystroke for Mac, or `Ctrl+C` for Windows and Linux terminals.

## How it works

1. When your on-premises container is running, navigate to [State machines](https://console.aws.amazon.com/states/home#/statemachines) and press on the `MqttBasedStateMachine-XXXXX` state machine.
1. Press `Start execution` button.
1. Paste the following `Input`:
  ``` json
  {
    "a": 15,
    "b": 42
  }
  ```
  and press on `Start execution`.
1. The execution starts. You can see a message received in the console output of your on-premises container. The container adds up `a` and `b` and send the results back.
1. The state machine receives the results and finishes the execution. If you press the `Dispatch Job to On-Premises` state in the `Graph view`, you can see the output of the state machine on the right:
  ``` json
  {
    "a": 15,
    "b": 42,
    "lambdaOutput": {
      "result": 57
      }
  }
  ```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
