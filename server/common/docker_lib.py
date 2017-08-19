import os
import subprocess
from common import fm_logger

fmlogging = fm_logger.Logging()

class DockerLib(object):

    def __init__(self):
        self.docker_file_snippets = {}
        self.docker_file_snippets['aws'] = self._aws_df_snippet()
        self.docker_file_snippets['google'] = self._google_df_snippet()

    def _aws_df_snippet(self):
        df = ("FROM lmecld/clis:awscli\n")
        return df

    def _google_df_snippet(self):
        cmd_1 = ("RUN sed -i 's/{pat}access_token{pat}.*/{pat}access_token{pat}/' credentials \n").format(pat="\\\"")

        cmd_2 = ("RUN sed -i \"s/{pat}access_token{pat}.*/{pat}access_token{pat}:{pat}$token{pat},/\" credentials \n").format(pat="\\\"")

        fmlogging.debug("Sed pattern 1:%s" % cmd_1)
        fmlogging.debug("Sed pattern 2:%s" % cmd_2)

        df = ("FROM lmecld/clis:gcloud \n"
              "RUN /google-cloud-sdk/bin/gcloud components install beta \n"
              "COPY . /src \n"
              "COPY google-creds/gcloud  /root/.config/gcloud \n"
              "WORKDIR /root/.config/gcloud \n"
              "{cmd_1}"
              "RUN token=`/google-cloud-sdk/bin/gcloud beta auth application-default print-access-token` \n"
              "{cmd_2}"
              "WORKDIR /src \n"
        )
        df = df.format(cmd_1=cmd_1, cmd_2=cmd_2)

        return df

    def get_dockerfile_snippet(self, key):
        return self.docker_file_snippets[key]
    
    def _execute_cmd(self, cmd):
        try:
            chanl = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, shell=True).communicate()
            err = chanl[1]
            output = chanl[0]
        except Exception as e:
            fmlogging.debug(e)
            raise e
        return err, output

    def docker_login(self, username, password, proxy_endpoint):
        login_cmd = ("docker login -u {username} -p {password} {proxy_endpoint}").format(username=username,
                                                                                         password=password,
                                                                                         proxy_endpoint=proxy_endpoint)
        fmlogging.debug("Login command:%s" % login_cmd)
        err, output = self._execute_cmd(login_cmd)
        return err, output

    def build_container_image(self, cont_name, docker_file_name, df_context='', tag=''):
        build_cmd = ("docker build -t {cont_name}:{tag} -f {docker_file_name} {df_context}").format(cont_name=cont_name,
                                                                                              docker_file_name=docker_file_name,
                                                                                              df_context=df_context,
                                                                                              tag=tag)
        fmlogging.debug("Docker build cmd:%s" % build_cmd)
        err, output = self._execute_cmd(build_cmd)
        return err, output

    def remove_container_image(self, cont_name, reason_phrase=''):
        fmlogging.debug("Removing container image %s. Reason: %s" % (cont_name, reason_phrase))
        rm_cmd = ("docker rmi -f {cont_name}").format(cont_name=cont_name)
        fmlogging.debug("rm command:%s" % rm_cmd)
        err, output = self._execute_cmd(rm_cmd)
        return err, output

    def push_container(self, cont_name):
        push_cmd = ("docker push {cont_name}").format(cont_name=cont_name)
        fmlogging.debug("Docker push cmd:%s" % push_cmd)
        err, output = self._execute_cmd(push_cmd)
        return err, output

    def run_container(self, cont_name):
        run_cmd = ("docker run -i -d --publish-all=true {cont_name}").format(cont_name=cont_name)
        fmlogging.debug("Docker run cmd:%s" % run_cmd)
        err, output = self._execute_cmd(run_cmd)
        return err, output

    def run_container_sync(self, cont_name):
        run_cmd = ("docker run {cont_name}").format(cont_name=cont_name)
        fmlogging.debug("Docker run cmd:%s" % run_cmd)
        err, output = self._execute_cmd(run_cmd)
        return err, output

    def stop_container(self, cont_id, reason_phrase=''):
        fmlogging.debug("Stopping container %s. Reason: %s" % (cont_id, reason_phrase))
        stop_cmd = ("docker stop {cont_id}").format(cont_id=cont_id)
        fmlogging.debug("stop command:%s" % stop_cmd)
        err, output = self._execute_cmd(stop_cmd)
        return err, output

    def remove_container(self, cont_id, reason_phrase=''):
        fmlogging.debug("Removing container %s. Reason: %s" % (cont_id, reason_phrase))
        rm_cmd = ("docker rm -f {cont_id}").format(cont_id=cont_id)
        fmlogging.debug("rm command:%s" % rm_cmd)
        err, output = self._execute_cmd(rm_cmd)
        return err, output
