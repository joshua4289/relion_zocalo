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




#relion-it-constants

PIPELINE_STAR = 'default_pipeline.star'
RUNNING_FILE = 'RUNNING_RELION_IT'
SETUP_CHECK_FILE = 'RELION_IT_SUBMITTED_JOBS'
PREPROCESS_SCHEDULE_PASS1 = 'PREPROCESS'
PREPROCESS_SCHEDULE_PASS2 = 'PREPROCESS_PASS2'
OPTIONS_FILE = 'relion-it-options.py' 
SECONDPASS_REF3D_FILE = 'RELION_IT_2NDPASS_3DREF'



class RelionRunner(CommonService):
    '''A zocalo service for running Relion '''

    # Human readable service name changed to dev 

    _service_name = "relion.start"

    # Logger name
    _logger_name = 'relion.zocalo.services.runner'

    def initializing(self):
        """Subscribe to the relion queue 

		"""

        queue_name = "relion.devstart"
        self.log.info("queue that is being listended to is %s" % queue_name)
        workflows.recipe.wrap_subscribe(self._transport, queue_name,
                                        self.run_relion, acknowledgement=True, log_extender=self.extend_log,
                                        allow_non_recipe_messages=True)
    
    def get_session_type(message):
        """ given a message add in the session-type """
        pass     




    def run_relion(self,rw,header, message):
        """ main method to do all the setup and run relion-it """

        self.log.info("Start relion through zocalo")

        import sys
        if sys.version_info[0] > 2:
            from pathlib import Path
        
        else:
            from pathlib2 import Path
        
        import subprocess
        from subprocess import Popen
        import sys

        ispyb_msg = message ['relion_workflow']
        ispyb_msg_path = Path(ispyb_msg)
        ispyb_msg_dir = Path(ispyb_msg_path).parent

        #SETUP: folders belonging to dls structure

        visit_dir ,workspace_dir,relion_dir = self.setup_folder_str(ispyb_msg_path)

        self.log.info("visit: %s" %visit_dir)
        self.log.info("workspace: %s " %workspace_dir)
        self.log.info("relion_dir: %s " %relion_dir)

        

        self.link_movies(relion_dir)

        try:
            # this will revert to the hard-coded default only if the module does not 
            # have an environment variable set 
            
            relion_pipeline_home = os.getenv('RELION_PIPELINE_HOME','/dls_sw/apps/EM/relion_cryolo/live/Cryolo_relion3.0/relion_yolo_it')
            sys.path.append(relion_pipeline_home)

            self.log.info("PIPELINE HOME= {} ".format(relion_pipeline_home))


            relion_it_script = str(Path(relion_pipeline_home).joinpath('cryolo_relion_it.py'))
            self.log.info( '***********relion-it script imported is %s'%relion_it_script)
            from cryolo_relion_it import RelionItOptions

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

        # before you write out read the message agian for session-type 
        
        acquisition_softwares = ['EPU','SerialEM']
        
        acquisition_sw = self.params_as_dict(ispyb_msg).get('acquisition_software')
        
              
                      
        
        

        with open( str(user_options_file),'w+') as uop:
            relion_params.print_options(out_file=uop)
            self.log.info("user-params written in  %s " %str(user_options_file))
            if acquisition_sw in acquisition_softwares:
                uop.write(f"""acquisition_software='{acquisition_sw}'""")
            else:
                uop.write(f"""acquisition_software='None'""")
                self.log.error("Aquisition Software not supported")
                    

        # TODO: don't know why the Popen cwd does not do this . 2 secs for NFS
        os.chdir(str(relion_dir))
        import time
        time.sleep(2)


        logfile_out = open(str(Path.joinpath(relion_dir,'relion_runner.out')),'a+')
        logfile_err = open(str(Path.joinpath(relion_dir,'relion_runner.err')),'a+')



        self.check_running_relion_its()




        cmd = ('source /etc/profile.d/modules.sh;'
                'module load hamilton;'
                'module unload EM/cryolo/relion_it;'
                'module load EM/cryolo/relion_it;',
                'python',relion_it_script,str(user_options_file),'--continue')

        cmd_to_run = " ".join(cmd)

        import subprocess

        # this is intentional because the running_relion it checks crashes consumers
        

        # the ack is just before the main thread starts 
        #this is because if the main thread fails for whatever reason the ack will not be sent zocalo will then try to re-deliver the message 
        # the re-delivered message is guarinteed to crash because the RUNNING_RELION_IT file is present 
        # the front-end is designed to warn the user of this and expects a 'STOP' which clears the RUNNING_RELION_IT file 


        subprocess.Popen(cmd_to_run,stdout=logfile_out,stderr=logfile_err,shell=True)
        time.sleep(0.1)

        # START relion and wait for status files or timeout 
        time_counter = 0 
        time_to_disk = 15 

        while time_counter < time_to_disk:
            time.sleep(1)
            time_counter += 1
            if Path.joinpath(relion_dir,RUNNING_FILE).exists() and Path.joinpath(relion_dir,SETUP_CHECK_FILE).exists(): 
                self.copy_running_to_frontend(str(relion_dir),str(ispyb_msg_dir))
                break


        self.log.info("RUNNNING file copy occurred")
        self.transport.ack(header)

        self.log.info("relion processing started")


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
            self.log.info("RUNNING STATE files copied {} to {}".format(str(f),str(ispyb_msg_path)))


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

        import sys
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

        # the path is relative to keep vizualization easy from the relion GUI
        


        raw_dir = Path('../../raw')
        
        #raw_dir = session_dir.joinpath('raw/')
        # check if symlink exists for Movies in relion_dir
        if not relion_dir.joinpath('Movies').is_symlink():
            relion_dir.joinpath('Movies').symlink_to(raw_dir)
        else:
            self.log.info("symlink already exists continue without session setup")








