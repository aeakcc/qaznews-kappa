// CI for qaznews-kappa, run by the Jenkins controller in jenkins/ for every branch;
// main is also deployed to a local Kubernetes cluster (kind).
// Build and test steps run in Docker; the controller needs only the docker CLI, kind and kubectl.
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
    stage('Deploy to Kubernetes') {
      when { branch 'main' }
      environment {
        JOB = "qaznews-kappa-${env.TAG}-${env.BUILD_NUMBER}"
      }
      steps {
        sh '''
          kind get clusters | grep -qx qaznews || kind create cluster --name qaznews --wait 2m
          kind export kubeconfig --name qaznews --internal
          kind load docker-image $IMAGE:$TAG --name qaznews
          kubectl create configmap qaznews-batches --from-file=examples/batch_ok.csv \
            --from-file=examples/batch_low.csv --dry-run=client -o yaml | kubectl apply -f -
          sed "s|$IMAGE:latest|$IMAGE:$TAG|" k8s/cronjob.yaml | kubectl apply -f -
          kubectl create job $JOB --from=cronjob/qaznews-kappa
          kubectl wait --for=condition=complete --timeout=2m job/$JOB
        '''
      }
      post {
        always {
          sh 'kubectl logs job/$JOB || true'
        }
      }
    }
  }
  post {
    cleanup {
      sh 'docker image rm -f $IMAGE:test-$TAG || true'
    }
  }
}
