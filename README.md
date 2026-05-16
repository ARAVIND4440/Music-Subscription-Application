# Music Subscription Application

## Project Overview

The Music Subscription Application is a cloud-based web application developed using Amazon Web Services (AWS). The application allows users to register, log in, search for music records, subscribe to songs, view subscriptions, and remove subscribed songs through a modern web interface.

The project was implemented to demonstrate multiple AWS deployment architectures, including:

* Amazon EC2
* Amazon ECS with Docker
* Amazon API Gateway with AWS Lambda

The application follows a client-server architecture where the frontend communicates with backend REST APIs to perform different operations.

---

# Technologies Used

## Frontend

* HTML
* CSS
* JavaScript

## Backend

* Python Flask
* REST API

## AWS Services

* Amazon S3
* Amazon DynamoDB
* Amazon EC2
* Amazon ECS Fargate
* Amazon ECR
* AWS Lambda
* Amazon API Gateway

## Containerisation

* Docker

---

# Application Features

* User Registration
* User Login Authentication
* Music Search Functionality
* Music Subscription Management
* Remove Subscriptions
* Responsive Dark-Themed User Interface
* REST API Integration
* Cloud-Based Deployment

---

# AWS Architecture Implementations

## 1. EC2 Deployment

The Flask backend application was hosted on an Amazon EC2 virtual machine. The frontend hosted on Amazon S3 communicated with the backend using the public IP address of the EC2 instance.

### Technologies Used

* EC2
* Flask
* DynamoDB
* S3

---

## 2. ECS Deployment

The backend application was containerised using Docker and deployed using Amazon ECS Fargate. Docker images were stored in Amazon Elastic Container Registry (ECR).

### Technologies Used

* Docker
* ECS Fargate
* ECR
* Flask
* DynamoDB

---

## 3. Lambda and API Gateway Deployment

The backend functionalities were implemented using AWS Lambda functions and exposed through Amazon API Gateway REST APIs.

### Technologies Used

* AWS Lambda
* REST API Gateway
* DynamoDB
* S3

---

# DynamoDB Tables

## login

Stores user account details.

| Attribute | Description        |
| --------- | ------------------ |
| email     | User email address |
| user_name | Username           |
| password  | User password      |

---

## music

Stores music records.

| Attribute | Description  |
| --------- | ------------ |
| title     | Song title   |
| artist    | Artist name  |
| album     | Album name   |
| year      | Release year |
| image_url | S3 image key |

---

## subscriptions

Stores user subscription information.

| Attribute | Description             |
| --------- | ----------------------- |
| email     | User email              |
| music_id  | Unique music identifier |
| title     | Song title              |
| artist    | Artist name             |
| album     | Album name              |
| year      | Release year            |

---

# REST API Endpoints

| Method | Endpoint       | Description            |
| ------ | -------------- | ---------------------- |
| POST   | /login         | User login             |
| POST   | /register      | User registration      |
| GET    | /music/search  | Search music records   |
| POST   | /subscribe     | Subscribe to music     |
| GET    | /subscriptions | Retrieve subscriptions |
| DELETE | /subscription  | Remove subscription    |

---

# Docker Commands

## Build Docker Image

```bash
docker buildx build --no-cache --platform linux/amd64 -t music-backend .
```

## Tag Docker Image

```bash
docker tag music-backend:latest 993022968106.dkr.ecr.us-east-1.amazonaws.com/music-backend:latest
```

## Push Docker Image to ECR

```bash
docker push 993022968106.dkr.ecr.us-east-1.amazonaws.com/music-backend:latest
```

---

# Example curl API Test

## Login API

```bash
curl -X POST "https://jtevt1xgeg.execute-api.us-east-1.amazonaws.com/prod/login" -H "Content-Type: application/json" -d "{\"email\":\"koushiksrini12@gmail.com\",\"password\":\"12345\"}"
```

---

# Challenges Faced

Several deployment and integration challenges were encountered during implementation, including:

* CORS configuration issues
* ECS public IP changes after redeployment
* Docker authentication problems with ECR
* API Gateway route mismatches
* AWS session token expiration
* Browser caching issues

These issues were resolved through service redeployment, Docker image rebuilding, API route verification, and AWS credential reconfiguration.

---

# Learning Outcomes

This project provided practical experience in:

* Cloud application deployment
* AWS service integration
* REST API development
* Docker containerisation
* ECS deployment workflows
* Serverless computing with Lambda
* API Gateway configuration
* DynamoDB integration
* Cloud troubleshooting and debugging

---

# Authors

Aravindkumar Subbaraj 
Manikanda Prabhu Bagavathi Krishnan
Koushik Srinivasan
Master of Data Science RMIT University