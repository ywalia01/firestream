#!/bin/bash

# Set AWS credentials
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
export AWS_SESSION_TOKEN=

# Log in to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 492025348070.dkr.ecr.us-east-1.amazonaws.com

# Build, tag, and push Docker image
# docker build -t firestream-transcoder .
docker build -t fyrestream-transcoder .
# docker tag firestream-transcoder:latest 492025348070.dkr.ecr.us-east-1.amazonaws.com/firestream-transcoder:latest
docker tag fyrestream-transcoder:latest 492025348070.dkr.ecr.us-east-1.amazonaws.com/fyrestream-transcoder:latest
# docker push 492025348070.dkr.ecr.us-east-1.amazonaws.com/firestream-transcoder:latest
docker push 492025348070.dkr.ecr.us-east-1.amazonaws.com/fyrestream-transcoder:latest
