import os
from os.path import expanduser
import shutil
import time

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from server.common import constants
from server.common import common_functions
from server.common import docker_lib
from server.common import fm_logger
from server.dbmodule.objects import container as cont_db
from server.server_plugins.gcloud import gcloud_helper
import server.server_plugins.resource_base as resource_base

home_dir = expanduser("~")

APP_AND_ENV_STORE_PATH = ("{home_dir}/.cld/data/deployments/").format(home_dir=home_dir)

fmlogger = fm_logger.Logging()

GCR = "us.gcr.io"


class GCRHandler(resource_base.ResourceBase):
    """GCR Resource handler."""

    #credentials = GoogleCredentials.get_application_default()

    gcloudhelper = gcloud_helper.GCloudHelper()

    def __init__(self):
        self.docker_handler = docker_lib.DockerLib()

    def _get_df_dir(self, cont_info):
        df_dir = cont_info['cont_store_path']
        df_dir = df_dir + "/" + cont_info['cont_df_folder_name']
        return df_dir

    def _get_access_token(self, cont_info):
        access_token = ''
        df = self.docker_handler.get_dockerfile_snippet("google_for_token")
        df_dir = self._get_df_dir(cont_info)
        cont_name = cont_info['cont_name'] + "-get-access-token"
        access_token = GCRHandler.gcloudhelper.get_access_token(df_dir, df, cont_name)
        return access_token

    def _build_container(self, cont_info, tag=''):
        df_dir = self._get_df_dir(cont_info)
        project = cont_info['project']
        cont_name = cont_info['cont_name']
        fq_cont_name = GCR + "/" + project + "/" + cont_name
        fmlogger.debug("Container name that will be used in building:%s" % fq_cont_name)

        err, output = self.docker_handler.build_container_image(fq_cont_name, df_dir + "/Dockerfile",
                                                                df_context=df_dir, tag=tag)
        return err, output, fq_cont_name

    def _push_container(self, cont_info, tagged_image):
        access_token = self._get_access_token(cont_info)

        self.docker_handler.docker_login("oauth2accesstoken",
                                         access_token, "https://" + GCR)

        self.docker_handler.push_container(tagged_image)

    def create(self, cont_name, cont_info):
        df_dir = self._get_df_dir(cont_info)
        if not os.path.exists(df_dir + "/google-creds"):
            shutil.copytree(home_dir + "/.config/gcloud", df_dir + "/google-creds/gcloud")

        cont_data = {}
        cont_data['status'] = 'building-container'

        cont_db.Container().update(cont_name, cont_data)
        tag = str(int(round(time.time() * 1000)))
        err, output, image_name = self._build_container(cont_info, tag=tag)
        tagged_image = image_name + ":" + tag
        if err:
            fmlogger.debug("Error encountered in building and tagging image. Not continuing with the request. %s" % err)
            cont_data['status'] = 'Error encountered in building and tagging image.' + str(err)
            cont_db.Container().update(cont_name, cont_data)
            return

        cont_details = {'tagged_image': tagged_image}
        cont_data['output_config'] = str(cont_details)
        cont_data['status'] = 'pushing-cont-to-gcr-repository'

        cont_db.Container().update(cont_name, cont_data)
        try:
            self._push_container(cont_info, tagged_image)
        except Exception as e:
            fmlogger.error("Exception encountered in pushing container to gcr %s" % e)
            cont_data['status'] = 'error-in-container-push-to-gcr:' + str(e)
            cont_db.Container().update(cont_name, cont_data)
            return

        cont_data['status'] = 'container-ready'
        cont_db.Container().update(cont_name, cont_data)

    def delete(self, cont_name, cont_info):
        pass

