# Jenkins controller for qaznews-kappa. Plugins and configuration are baked in (casc.yaml),
# so the server is rebuilt from this folder; builds use the host Docker engine via its socket.
FROM jenkins/jenkins:2.580.1-lts-jdk21
USER root
COPY --from=docker:29.9.2-cli /usr/local/bin/docker /usr/local/bin/
COPY --from=docker:29.9.2-cli /usr/local/libexec/docker/cli-plugins/docker-buildx /usr/local/libexec/docker/cli-plugins/
USER jenkins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY casc.yaml /usr/share/jenkins/casc.yaml
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/casc.yaml \
    JAVA_OPTS=-Djenkins.install.runSetupWizard=false
