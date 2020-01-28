from __future__ import absolute_import, division, print_function
from subprocess import Popen
from workflows.services.common_service import CommonService
import workflows.recipe

# change to the safe-inport for 2_3 compatibility

import sys
if sys.version_info[0] > 2:
    from pathlib import Path
    from pathlib import PurePath
else:
    from pathlib2 import Path
    


class Relionflipgain(CommonService):
    
    _service_name = "relion.flip_gain"
    _logger_name = 'relion.zocalo.services.runner'
    
    def initializing(self):
        """Subscribe to the per_image_analysis queue. Received messages must be acknowledged."""
        queue_name = "relion.flip_gain"
        self.log.info("queue that is being listened to is %s" % queue_name)
        workflows.recipe.wrap_subscribe(self._transport, queue_name,
                                        self.flip_gain, acknowledgement=True, log_extender=self.extend_log,
                                        allow_non_recipe_messages=True)
    
    
    def is_epu_session(self,session_path="/dls/tmp/jtq89441/dls/m02/data/2019/em12345-01/raw/"):
        
        """ function returns True if raw folder has raw/GridSquare_*/Data/ """
        
        import re 
        from pathlib import PurePath

        match = re.search('GridSquare_*',session_path)
        
        if match is not None:
            return True 
        else:
            return False 
        
        
        # if any("Grid" in p for p in PurePath(session_path).parts):
        #     return True 
        # else:
        #     return  False
        

    
    def flip_gain(self,rw,header,message):
        
        """ given a gain file name this will flip it  
        clip flipx original_gain_file.mrc gain.mrc """
        
        # the flip only occurs fif the session is an EPU session 
        
        from pathlib import Path 
        
        gain_file  = message['gain_file']
        
        relion_workspace =  Path(gain_file).parent
        
        
        if True: #self.is_epu_session(gain_file):
            
            cmd = ('module load EM/imod;')
            flip_cmd = ['clip','flipx',gain_file,'Gain_flip.mrc']
            
            #cmd += args
            cmd += " ".join(arg for arg in flip_cmd)
            self.log.info(f"fliping the gain command is {cmd}")
            
            imod_out = str(relion_workspace.joinpath('imod_flip.out'))
            imod_err = str(relion_workspace.joinpath('imod_flip.err'))
            
            
            with open(imod_out,'w+') as out ,  open(imod_err,'w+') as err:
                Popen(cmd,cwd=str(relion_workspace),stdout=out ,stderr=err,shell=True)

        else:
            self.log.info("Not flipping gain as Serial-EM session")
            
        
        self.transport.ack(header)