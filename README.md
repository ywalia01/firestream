# Fyrestream - A Video Transcoding Pipeline on AWS

## Project Overview

**Fyrestream** is a fully automated video transcoding pipeline hosted entirely on AWS. The pipeline efficiently processes video uploads, transcodes them into different resolutions, and stores the output back in Amazon S3. It leverages a variety of AWS services such as S3, SQS, Lambda, ECS, ECR, and more, ensuring the architecture adheres to the AWS Well-Architected Framework's principles of security, reliability, performance efficiency, and cost optimization.

## Table of Contents

- [Architecture](#architecture)
- [Project Flow](#project-flow)
- [AWS Services Used](#aws-services-used)
- [Security and Cost Efficiency](#security-and-cost-efficiency)
- [Setup and Deployment](#setup-and-deployment)
- [Usage](#usage)
- [Infrastructure Diagram](#infrastructure-diagram)
- [Contact](#contact)

## Architecture

![Fyrestream Architecture](https://github.com/user-attachments/assets/81a5b58d-ac3c-40ed-bb24-9cdec12d4ead)

The **Fyrestream** architecture comprises a scalable, serverless solution designed to handle video transcoding tasks. The system reacts to video uploads in S3, sends events to an SQS queue, and leverages Lambda functions to invoke containerized transcoding tasks in ECS Fargate. The transcoded videos are then stored back in S3, ready for user consumption in various formats and resolutions.

## Project Flow

1. **S3 Video Upload**:  
   The user uploads a video to the `fyrestream-videos` S3 bucket under the `/videos` folder.

2. **S3 Event Notification**:  
   An event is generated upon the creation of a new object in the S3 bucket. This event sends a message to an SQS queue named `fyrestream-sqs`.

3. **SQS Trigger**:  
   The SQS queue triggers a Lambda function called `fyrestream-sqs-poller` which processes the message.

4. **Lambda Chain Invocation**:  
   The `fyrestream-sqs-poller` Lambda function invokes another Lambda function named `fyrestream-transcoder-invoker`, which processes the S3 event.

5. **ECS Task Execution**:  
   The `fyrestream-transcoder-invoker` Lambda function runs a task in ECS Fargate (`fyrestream-transcoder` task) to transcode the video. The task is launched using a container stored in an ECR repository named `fyrestream-transcoder`.

6. **Video Transcoding**:  
   The ECS task transcodes the video into multiple resolutions.

7. **S3 Output Storage**:  
   The transcoded videos are uploaded back into a different S3 bucket, ready to be accessed or delivered to end users.

## AWS Services Used

### Core Services

- **Amazon S3**: Stores the original and transcoded videos.
- **Amazon SQS**: Serves as the messaging queue between S3 and Lambda.
- **AWS Lambda**: Orchestrates tasks such as polling SQS and invoking ECS tasks.
- **Amazon ECS (Fargate)**: Runs the transcoding tasks in a containerized environment.
- **Amazon Elastic Container Registry (ECR)**: Stores the Docker images used for video transcoding.

### Additional Services

- **AWS Secrets Manager**: Stores and manages secrets such as API keys and credentials used within the Lambda functions.
- **Amazon VPC**: Provides network isolation and security, with both public and private subnets, and internet access via a NAT Gateway.
- **AWS CloudFormation**: Automates the deployment and management of the entire infrastructure stack.

## Security and Cost Efficiency

- **VPC Configuration**:  
  The Lambda functions and ECS tasks operate within a VPC (`fyrestream-vpc`) to ensure secure communication and data handling. The VPC contains both public and private subnets for optimal security and performance. A NAT Gateway in the public subnets ensures the Lambda functions have secure internet access while protecting internal resources.

- **IAM Roles**:  
  The ECS tasks and Lambda functions use distinct task and execution roles (`LabRole`) to control access to AWS services and resources, ensuring least privilege principles are followed.

- **Cost Efficiency**:  
  The architecture uses Fargate, a serverless compute engine for containers, which automatically scales based on workload demand, reducing idle resource costs. Additionally, CloudFormation simplifies resource management and teardown, further optimizing cost control.

## Setup and Deployment

### Prerequisites

- AWS Account
- AWS CLI installed and configured
- Docker installed and running
- AWS CloudFormation templates for infrastructure deployment

### Deployment Steps

1. **Clone the Repository**:  
   Clone the project repository to your local machine.

   ```bash
   git clone https://github.com/yourusername/fyrestream.git
   cd fyrestream
   ```

2. **Build and Push Docker Image**:  
   Build the Docker image for the transcoder and push it to your ECR repository.

   ```bash
   docker build -t fyrestream-transcoder .
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
   docker tag fyrestream-transcoder:latest <account-id>.dkr.ecr.<region>.amazonaws.com/fyrestream-transcoder:latest
   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/fyrestream-transcoder:latest
   ```

3. **Deploy the Infrastructure**:  
   Use AWS CloudFormation to deploy the necessary AWS resources (S3, SQS, Lambda, ECS, ECR, VPC, Secrets Manager).

   ```bash
   aws cloudformation deploy --template-file fyrestream-cloudformation.yaml --stack-name fyrestream-stack
   ```

4. **Configure Secrets**:  
   Store required secrets in AWS Secrets Manager, including database credentials or API keys if necessary.

5. **Test the Pipeline**:  
   Upload a video to the `fyrestream-videos` S3 bucket and verify the transcoding process by checking the transcoded outputs in the destination bucket.

## Usage

Once deployed, **Fyrestream** is fully automated. To start transcoding videos:

1. Upload a video file to the `/videos` folder in the `fyrestream-videos` S3 bucket.
2. The pipeline will handle the rest, including:
   - Event notification
   - Queue messaging
   - Task invocation
   - Transcoding execution
   - Storing the transcoded outputs in S3

### Example

To upload a video:

1. Navigate to the S3 bucket `fyrestream-videos`.
2. Upload a video to the `/videos` folder.
3. Wait for the pipeline to process the video.
4. Find the transcoded files in the destination S3 bucket.

## Infrastructure Diagram

(Include a diagram illustrating the architecture flow if possible. This should show the interactions between S3, SQS, Lambda, ECS, and other components.)

## Contact

For more information, feel free to contact me:

- Name: [Your Name]
- Email: [your.email@example.com]
- LinkedIn: [Your LinkedIn Profile]
- GitHub: [Your GitHub Profile]
