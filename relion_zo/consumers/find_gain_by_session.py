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
    


class Relionfindgain(CommonService):
    
    _service_name = "relion.find_gain"
    _logger_name = 'relion.zocalo.services.runner'
    
    def initializing(self):
        """Subscribe to the per_image_analysis queue. Received messages must be acknowledged."""
        queue_name = "relion.find_gain"
        self.log.info("queue that is being listened to is %s" % queue_name)
        workflows.recipe.wrap_subscribe(self._transport, queue_name,
                                        self.find_and_convert_gain, acknowledgement=True, log_extender=self.extend_log,
                                        allow_non_recipe_messages=True)
    
    
    def is_epu_session(self,session_path):
        
        """ function returns True if raw folder has raw/GridSquare_*/Data/ """
        
   
        from pathlib import PurePath
    
        if any("Grid" in p for p in PurePath(session_path).parts):
            return True 
        else:
            return  False
        

    
    def convert_dm4_to_mrc(self,file_ip,file_op='Gain.mrc'):
        """ (str,str) calls dmmrc from imod using latest defualt module of imod """
        cmd = ('module load EM/imod;')

        
        escape_slashes = str(file_ip).replace(" ",'\ ')
        
        convert_command = ["dm2mrc",escape_slashes,file_op]
        
        cmd += " ".join(arg for arg in convert_command)
        
        self.log.info("convert command is {} ".format(cmd))
        

        return cmd 

    def convert_tif_to_mrc(self,file_ip,file_op='Gain.mrc'):
        """ (str,str) calls dmmrc from imod using latest defualt module of imod """
        
        cmd = ('module load EM/imod;')

        convert_command = ["tifmrc", file_ip,file_op] 

        cmd += " ".join(arg for arg in convert_command)

        return cmd 

    
    def skip_path_with_spaces(self,str_path):
        
        ''' 
        input : string of path 
        returns a list of paths without any spaces 
        
        '''
        import re
        match_list = re.findall('[\s]',str_path)
        if match_list:
            return match_list    

    def find_gain_by_session(self,session_path):
        
            """ 1.User checks tick box in front end 
            2. checks the processing folder for a file ending with .dm4 returns it 
            """
            
            import os 
            
            
            processing_folder_path = session_path.parents[2].joinpath('processing')
            print(str(processing_folder_path))

            def no_space(name):
                if " " in str(name):
                    print (f"spaces not supported in name {name}")
                    return False 
                return True



            for root, dirs, files in os.walk(str(processing_folder_path)):
                files_accepted = list(filter(lambda x: x.endswith('.dm4'),files))
                self.log.info(f'files that were found initial{list(files)}')
                self.log.info(f"files with dm4 extension are {files_accepted}")
                
                
                
                    
                return Path.joinpath(processing_folder_path).joinpath(files_accepted[-1])
         


    def find_and_convert_gain(self,rw,header,message):
        
        ispyb_msg = Path(message['session_path'])
        
        # change this find_gain_by_session logic 
        
        # return the raw list 
        # find the file ending with dm4 with spaces 
        # call dm2mrc and name it to a linux-fiendly name
        # if it's an EPU session flip otherwise don't
         
        
        
        gain_path = self.find_gain_by_session(ispyb_msg)
        self.log.info("Gain path found was in {}".format(gain_path))
        
        if gain_path is not None :
            
            session_number = gain_path.parents[1].parts[-1]
            relion_workspace = gain_path.parents[1].joinpath('processed').joinpath(str('relion_'+ session_number))
            imod_out = str(relion_workspace.joinpath('imod_convert.out'))
            imod_err = str(relion_workspace.joinpath('imod_convert.err'))
            self.log.info("gda2_workspace is "+ str(relion_workspace))


            with open(imod_out,'w+') as out ,  open(imod_err,'w+') as err:
                if str(gain_path).endswith('.dm4'):
                    Popen(self.convert_dm4_to_mrc(str(gain_path),file_op='Gain.mrc'),cwd=str(relion_workspace),stdout=out ,stderr=err,shell=True)
                elif str(gain_path).endswith('.tif') or str(gain_path).endswith('tiff'):
                    Popen(self.convert_tif_to_mrc(str(gain_path),file_op='Gain.mrc'),cwd=str(relion_workspace),stdout=out,stderr=err,shell=True)

        #finally acknowledge 
        self.transport.ack(header)

            

