pipeline {
    agent any
    
    environment {
        DOCKERHUB_CREDENTIALS = credentials('docker-hub-cred')
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main', url: 'https://github.com/Yuvakunaal/DevOps-Assignment-2.git'
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh '/usr/local/bin/docker build -t devops-assignment-2-app .'
            }
        }
        
        stage('Test Application') {
            steps {
                sh '''
                /usr/local/bin/docker stop test-app 2>/dev/null || true
                /usr/local/bin/docker rm test-app 2>/dev/null || true
                /usr/local/bin/docker run -d --name test-app -p 8001:8000 devops-assignment-2-app
                sleep 10
                curl -f http://localhost:8001 || exit 1
                /usr/local/bin/docker stop test-app
                /usr/local/bin/docker rm test-app
                '''
            }
        }
        
        stage('Push to Docker Hub') {
            steps {
                sh '''
                /usr/local/bin/docker tag devops-assignment-2-app yuvakunaal/devops-assignment-2-app:latest
                echo $DOCKERHUB_CREDENTIALS_PSW | /usr/local/bin/docker login -u $DOCKERHUB_CREDENTIALS_USR --password-stdin
                /usr/local/bin/docker push yuvakunaal/devops-assignment-2-app:latest
                '''
            }
        }
        
        stage('Deploy to Kubernetes') {
            steps {
                sh '/opt/homebrew/bin/kubectl apply -f k8s/'
            }
        }
    }
}