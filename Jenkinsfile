// CI/CD pipeline (Jenkins): lint -> security scan -> test+coverage -> static analysis -> build -> deploy
pipeline {
  agent any
  environment { IMAGE = "zenith404/legal-assistant" }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Install') {
      steps { dir('backend') { sh 'python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt' } }
    }
    stage('Lint') {
      steps { dir('backend') { sh '. .venv/bin/activate && flake8 app tests --max-line-length=120' } }
    }
    stage('Security scan (SAST)') {
      steps { dir('backend') { sh '. .venv/bin/activate && bandit -r app -ll' } }
    }
    stage('Unit tests + coverage') {
      steps {
        dir('backend') {
          sh '. .venv/bin/activate && pytest --cov=app --cov-branch --cov-report=xml --cov-report=term --cov-fail-under=85 --junitxml=junit.xml'
        }
      }
      post { always { junit 'backend/junit.xml' } }
    }
    stage('SonarQube') {
      when { expression { return env.SONAR_HOST_URL != null } }
      steps { withSonarQubeEnv('sonar') { sh 'sonar-scanner' } }
    }
    stage('Build images') {
      steps {
        sh 'docker build -t $IMAGE-backend:$BUILD_NUMBER backend'
        sh 'docker build -t $IMAGE-frontend:$BUILD_NUMBER frontend'
      }
    }
    stage('Deploy') {
      when { branch 'main' }
      steps { sh 'docker compose up -d --build' }
    }
  }
}
