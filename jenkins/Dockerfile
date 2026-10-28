# Jenkins controller for qaznews-kappa. Plugins and configuration are baked in (casc.yaml),
# so the server is rebuilt from this folder; builds use the host Docker engine via its socket,
# and kind/kubectl deploy to a local Kubernetes cluster that runs on the same engine.
FROM jenkins/jenkins:2.580.1-lts-jdk21
USER root
COPY --from=docker:29.9.2-cli /usr/local/bin/docker /usr/local/bin/
COPY --from=docker:29.9.2-cli /usr/local/libexec/docker/cli-plugins/docker-buildx /usr/local/libexec/docker/cli-plugins/
ARG KUBECTL=v1.37.1 KUBECTL_SHA256=65691ff77eb6fa44c908b77a1082c9f092c3b9733b5cefabec0d1104890e21a8
ARG KIND=v0.33.0 KIND_SHA256=aee6151561422756b764a4ae28e7f44cda5af5a9eead3cc9985112b1de8d8e0d
RUN curl -fsSL --retry 3 --max-time 300 -o /usr/local/bin/kubectl https://dl.k8s.io/release/$KUBECTL/bin/linux/amd64/kubectl \
 && curl -fsSL --retry 3 --max-time 300 -o /usr/local/bin/kind https://github.com/kubernetes-sigs/kind/releases/download/$KIND/kind-linux-amd64 \
 && printf '%s  %s\n' $KUBECTL_SHA256 /usr/local/bin/kubectl $KIND_SHA256 /usr/local/bin/kind | sha256sum -c \
 && chmod +x /usr/local/bin/kubectl /usr/local/bin/kind
USER jenkins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY casc.yaml /usr/share/jenkins/casc.yaml
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/casc.yaml \
    JAVA_OPTS=-Djenkins.install.runSetupWizard=false
