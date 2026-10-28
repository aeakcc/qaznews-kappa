// CI for qaznews-kappa, run by the Jenkins controller in jenkins/ for every branch.
// Each step runs in Docker, so the controller needs nothing but the docker CLI.
pipeline {
  agent any
  options {
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '30'))
  }
  environment {
    IMAGE = 'qaznews-kappa'
    TAG = "${env.GIT_COMMIT.take(7)}"
    TESTS = "${env.BUILD_TAG.replaceAll('[^A-Za-z0-9_.-]', '-')}"
  }
  stages {
    stage('Test image') {
      steps {
        sh 'docker build --target test -t $IMAGE:test-$TAG .'
      }
    }
    stage('Lint') {
      steps {
        sh 'docker run --rm $IMAGE:test-$TAG sh -c "ruff check . && ruff format --check ."'
      }
    }
    stage('Unit tests') {
      steps {
        sh 'docker run --name $TESTS $IMAGE:test-$TAG pytest --junitxml=junit.xml --cov=qaznews_kappa --cov-fail-under=90'
      }
      post {
        always {
          sh 'docker cp $TESTS:/app/junit.xml . && docker rm $TESTS'
          junit 'junit.xml'
        }
      }
    }
    stage('Runtime image') {
      steps {
        sh 'docker build -t $IMAGE:$TAG .'
      }
    }
    stage('Smoke test') {
      steps {
        sh 'docker run --rm -i $IMAGE:$TAG /dev/stdin --min-kappa 0.7 < examples/batch_ok.csv'
      }
    }
  }
  post {
    cleanup {
      sh 'docker image rm -f $IMAGE:test-$TAG || true'
    }
  }
}
