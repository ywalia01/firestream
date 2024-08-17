import {
  SQSClient,
  ReceiveMessageCommand,
  DeleteMessageCommand,
} from "@aws-sdk/client-sqs";
import { ECSClient, RunTaskCommand } from "@aws-sdk/client-ecs";
import type { S3Event } from "aws-lambda";

const client = new SQSClient({
  region: "us-east-1",
  credentials: {
    accessKeyId: "",
    secretAccessKey: "",
    sessionToken: "",
  },
});

const ecsClient = new ECSClient({
  region: "us-east-1",
  credentials: {
    accessKeyId: "",
    secretAccessKey: "",
    sessionToken: "",
  },
});

async function init() {
  const command = new ReceiveMessageCommand({
    QueueUrl: "https://sqs.us-east-1.amazonaws.com/492025348070/fyre-sqs",
    MaxNumberOfMessages: 1,
    WaitTimeSeconds: 20,
  });

  while (true) {
    const { Messages } = await client.send(command);
    if (!Messages) {
      console.log("No message in queue");
      continue;
    }

    try {
      for (const message of Messages) {
        const { MessageId, Body } = message;
        console.log("Message Received", { MessageId, Body });

        if (!Body) {
          continue;
        }

        // Validate and Parse the event
        const event = JSON.parse(Body) as S3Event;

        // Ignore the test event
        if ("Service" in event && "Event" in event) {
          if (event.Event === "s3:TestEvent") {
            await client.send(
              new DeleteMessageCommand({
                QueueUrl:
                  "https://sqs.us-east-1.amazonaws.com/492025348070/fyre-sqs",
                ReceiptHandle: message.ReceiptHandle,
              })
            );
            continue;
          }
        }

        for (const record of event.Records) {
          const { s3 } = record;
          const {
            bucket,
            object: { key },
          } = s3;

          // Spin the docker container
          const runTaskCommand = new RunTaskCommand({
            taskDefinition:
              "arn:aws:ecs:us-east-1:492025348070:task-definition/firestream-transcoder",
            cluster: "arn:aws:ecs:us-east-1:492025348070:cluster/dev",
            launchType: "FARGATE",
            networkConfiguration: {
              awsvpcConfiguration: {
                assignPublicIp: "ENABLED",
                securityGroups: ["sg-0e95614f453d5b26e"],
                subnets: [
                  "subnet-0014f6d47f71a87bd",
                  "subnet-0028ffb7fb9b2e528",
                  "subnet-0c582a5e06ff22802",
                ],
              },
            },
            overrides: {
              containerOverrides: [
                {
                  name: "firestream-transcoder",
                  environment: [
                    { name: "BUCKET_NAME", value: bucket.name },
                    { name: "KEY", value: key },
                  ],
                },
              ],
            },
          });
          await ecsClient.send(runTaskCommand);
          // Delete the message from the queue

          await client.send(
            new DeleteMessageCommand({
              QueueUrl:
                "https://sqs.us-east-1.amazonaws.com/492025348070/fyre-sqs",
              ReceiptHandle: message.ReceiptHandle,
            })
          );
        }
      }
    } catch (err) {
      console.log(err);
    }
  }
}

init();
