"use strict";
var __awaiter =
  (this && this.__awaiter) ||
  function (thisArg, _arguments, P, generator) {
    function adopt(value) {
      return value instanceof P
        ? value
        : new P(function (resolve) {
            resolve(value);
          });
    }
    return new (P || (P = Promise))(function (resolve, reject) {
      function fulfilled(value) {
        try {
          step(generator.next(value));
        } catch (e) {
          reject(e);
        }
      }
      function rejected(value) {
        try {
          step(generator["throw"](value));
        } catch (e) {
          reject(e);
        }
      }
      function step(result) {
        result.done
          ? resolve(result.value)
          : adopt(result.value).then(fulfilled, rejected);
      }
      step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
  };
Object.defineProperty(exports, "__esModule", { value: true });
const client_sqs_1 = require("@aws-sdk/client-sqs");
const client_ecs_1 = require("@aws-sdk/client-ecs");
const client = new client_sqs_1.SQSClient({
  region: "us-east-1",
  credentials: {
    accessKeyId: "",
    secretAccessKey: "",
    sessionToken: "",
  },
});
const ecsClient = new client_ecs_1.ECSClient({
  region: "us-east-1",
  credentials: {
    accessKeyId: "",
    secretAccessKey: "",
    sessionToken: "",
  },
});
function init() {
  return __awaiter(this, void 0, void 0, function* () {
    const command = new client_sqs_1.ReceiveMessageCommand({
      QueueUrl: "https://sqs.us-east-1.amazonaws.com/492025348070/fyre-sqs",
      MaxNumberOfMessages: 1,
      WaitTimeSeconds: 20,
    });
    while (true) {
      const { Messages } = yield client.send(command);
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
          const event = JSON.parse(Body);
          // Ignore the test event
          if ("Service" in event && "Event" in event) {
            if (event.Event === "s3:TestEvent") {
              yield client.send(
                new client_sqs_1.DeleteMessageCommand({
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
            const runTaskCommand = new client_ecs_1.RunTaskCommand({
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
            yield ecsClient.send(runTaskCommand);
            // Delete the message from the queue
            yield client.send(
              new client_sqs_1.DeleteMessageCommand({
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
  });
}
init();
