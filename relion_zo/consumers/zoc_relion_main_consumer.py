from __future__ import absolute_import, division, print_function
from workflows.services.common_service import CommonService
import workflows.recipe
from subprocess import PIPE, Popen
import json
import os, re
try:
    import runpy
except ImportError:
    print("Runpy cannot be found")



# Active MQ Scipion Consumer started as gda2
#relion-it-constants

PIPELINE_STAR = 'default_pipeline.star'
RUNNING_FILE = 'RUNNING_RELION_IT'
SETUP_CHECK_FILE = 'RELION_IT_SUBMITTED_JOBS'
PREPROCESS_SCHEDULE_PASS1 = 'PREPROCESS'
PREPROCESS_SCHEDULE_PASS2 = 'PREPROCESS_PASS2'
OPTIONS_FILE = 'relion-it-options.py' 
SECONDPASS_REF3D_FILE = 'RELION_IT_2NDPASS_3DREF'
#



class RelionRunner(CommonService):
    '''A zocalo service for running Scipion'''

    # Human readable service name
    _service_name = "relion.relion_prod_ispyb"

    # Logger name
    _logger_name = 'relion.zocalo.services.runner'

    def initializing(self):
        """Subscribe to the relion queue 

		"""

        queue_name = "relion.relion_prod_ispyb"
        self.log.info("queue that is being listended to is %s" % queue_name)
        workflows.recipe.wrap_subscribe(self._transport, queue_name,
                                        self.run_relion, acknowledgement=True, log_extender=self.extend_log,
                                        allow_non_recipe_messages=True)

    def copy_running_to_frontend(self,relion_dir,ispyb_msg_path):

        ''' finds the RUNNING_* and RELION_IT_SUBMITTED files in relion project and copies them to .ispyb/processing '''

        import os
        import shutil
        import glob

        cwd = relion_dir
        os.chdir(str(relion_dir))

        for f in glob.glob(r'RUNNING_*'):
            shutil.copy(f,ispyb_msg_path)
            #add logging
            self.log.info("copied {} to {}".format(str(f),str(ispyb_msg_path)))




    def run_relion(self,rw,header, message):
        """ main method to do all the setup and run relion-it """

        self.log.info("Start relion through zocalo")

        if sys.version_info[0] > 2:
            from pathlib import Path
        
        else:
            from pathlib2 import Path
        
        import subprocess
        from subprocess import Popen
        import sys

        ispyb_msg = message ['session_path']
        ispyb_msg_path = Path(ispyb_msg)
        ispyb_msg_dir = Path(ispyb_msg_path).parent

        #SETUP: folders belonging to dls structure

        visit_dir ,workspace_dir,relion_dir = self.setup_folder_str(ispyb_msg_path)

        self.log.info("visit: %s" %visit_dir)
        self.log.info("workspace: %s " %workspace_dir)
        self.log.info("relion_dir: %s " %relion_dir)

        

        self.link_movies(relion_dir)

        try:

            relion_pipeline_home = os.getenv('RELION_PIPELINE_HOME','/dls_sw/apps/EM/relion_cryolo/CryoloRelion-master/')
            sys.path.append(relion_pipeline_home)

            self.log.info("PIPELINE HOME= {} ".format(relion_pipeline_home))


            relion_it_script = str(Path(relion_pipeline_home).joinpath('relion_it_editted.py'))
            from relion_it_editted import RelionItOptions

            # all the options are rolled into one 

            cluster_options = runpy.run_module('options')

        except ImportError:
            import traceback
            trace = traceback.format_exc()
            self.log.error("{}".format(trace))
            sys.exit(1)

        #initialized with default parameters
        relion_params = RelionItOptions()
        relion_params.update_from(cluster_options)

        #WARNING: add the user options after the template otherwise will override

        relion_params.update_from(self.params_as_dict(ispyb_msg))

        user_options_file = relion_dir.joinpath('relion_it_options.py')




        with open( str(user_options_file),'w+') as uop:
            relion_params.print_options(out_file=uop)
            self.log.info("user-params written in  %s " %str(user_options_file))




        os.chdir(str(relion_dir))
        import time
        time.sleep(2)
        # TODO: don't know why the Popen cwd does not do this . 2 secs for NFS

        logfile_out = open(str(Path.joinpath(relion_dir,'relion_runner.out')),'a+')
        logfile_err = open(str(Path.joinpath(relion_dir,'relion_runner.err')),'a+')



        self.check_running_relion_its()




        cmd = ('source /etc/profile.d/modules.sh;'
                'module load hamilton;'
                'module unload EM/cryolo/yolo_it;'
                'module load EM/cryolo/yolo_it;',
                'dls-python',relion_it_script,str(user_options_file),'--continue')

        cmd_to_run = " ".join(cmd)

        import subprocess

        # this is intentional because the running_relion it checks crashes consumers
        self.transport.ack(header)
        subprocess.Popen(cmd_to_run,stdout=logfile_out,stderr=logfile_err,shell=True)

        self.copy_running_to_frontend(str(relion_dir),str(ispyb_msg_dir))

        self.log.info("relion processing started ")



    def check_running_relion_its(self):


        """ Checks if relion-it is running,needs to return an HTTP bad something if the RUNNING file(s) exist """




        if os.path.isfile(RUNNING_FILE):
            self.log.error(" RELION_IT: ERROR: {} is already present: delete this file and make sure no other copy of this script is running. Exiting now ...".format(RUNNING_FILE))
            #don't crash consumer just log an error
            #exit(0)

        # Also make sure the preprocessing pipeliners are stopped before re-starting this script
        for checkfile in ('RUNNING_PIPELINER_' + PREPROCESS_SCHEDULE_PASS1, 'RUNNING_PIPELINER_' + PREPROCESS_SCHEDULE_PASS2):
            
            if os.path.isfile(checkfile):
                self.log.error(" RELION_IT: ERROR: {} is already present: delete this file and make sure no relion_pipeliner job is still running. Exiting now ...".format(checkfile))

                #exit(0)

    def setup_folder_str(self,folder_path):
        """ sets up the folder structure relative to the messsage path """


        if sys.version_info[0] > 2:
            from pathlib import Path
        
        else:
            from pathlib2 import Path

        

        visit_dir = folder_path.parents[2]
        workspace_dir = visit_dir / 'processed'

        workspace_dir.mkdir(parents=True, exist_ok=True)

        project_name = 'relion_'+ str(visit_dir.stem)

        relion_dir = Path(workspace_dir/project_name)
        relion_dir.mkdir(parents=True, exist_ok=True)

        movies_dir = Path(visit_dir/'raw')
        movies_dir.mkdir(parents=True, exist_ok=True)
        
        
        




        return visit_dir,movies_dir,relion_dir


    def params_as_dict(self,user_ip):

        """ loads in json file and converts to dictionary  """

        import json
        with open (user_ip,'r') as f:
            user_dict = json.load(f)
        return user_dict


    def link_movies(self,relion_dir):
        """ links Movies session/raw folder  """

        """ links Movies session/raw folder name into a relion project  """

        # "filesPath": "/dls/tmp/gda2/dls/m02/data/2019/em12345-01/raw/GridSquare_22965332/Data/",
        # "filesPattern": "*.mrc"
        # ln -s ../raw Movies
        # symlink /dls/m02/data/2019/cm22936-1/raw/ Movies
        
        import sys 
        
        if sys.version_info[0] > 2:
            from pathlib import Path
        
        else:
            from pathlib2 import Path
        
        import os


        session_dir = Path(relion_dir).parents[1]



        raw_dir = session_dir.joinpath('raw/')
        # check if symlink exists for Movies in relion_dir
        if not relion_dir.joinpath('Movies').is_symlink():
            relion_dir.joinpath('Movies').symlink_to(raw_dir)
        else:
            self.log.info("symlink already exists continue without session setup")








