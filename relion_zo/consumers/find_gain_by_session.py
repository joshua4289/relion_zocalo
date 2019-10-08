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
    
    _service_name = "relion.relion_find_gain"
    _logger_name = 'relion.zocalo.services.runner'
    
    def initializing(self):
        """Subscribe to the per_image_analysis queue. Received messages must be acknowledged."""
        queue_name = "relion.relion_find_gain"
        self.log.info("queue that is being listened to is %s" % queue_name)
        workflows.recipe.wrap_subscribe(self._transport, queue_name,
                                        self.find_and_convert_gain, acknowledgement=True, log_extender=self.extend_log,
                                        allow_non_recipe_messages=True)
    
    

    
    def convert_dm4_to_mrc(self,file_ip,file_op='Gain.mrc'):
        """ (str,str) calls dmmrc from imod using latest defualt module of imod """
        cmd = ('module load EM/imod;')

        convert_command = ["dm2mrc", file_ip,file_op] 

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
            2. gets a path Checks in the raw folder only on top-level (because find is computationally expensive)
            3.returns the gain  full path 
            
            it will expect a .dm4 or file with 'gain'  in name in the top level skips files with spaces
            
            """
            
            import os 
            
            
            raw_folder_path = session_path.parents[2].joinpath('raw')
            print(str(raw_folder_path))

            def no_space(name):
                if " " in str(name):
                    print ('spaces not supported in name ')
                    return False 
                return True



            for root, dirs, files in os.walk(str(raw_folder_path)):
                files_accepted = filter(lambda x: x.endswith('.dm4') or 'gain' in x,files)
                self.log.info(f'files that were found initial{list(files)}')
                nospace_files = list(filter(no_space,files_accepted))
                print(f'files nospace is {list(nospace_files)}')
                # filter returns an iterator 

                if not nospace_files:
                    return None
                    
                for f in nospace_files:
                    if len(nospace_files) == 1:
                        return Path.joinpath(raw_folder_path).joinpath(f)
                    else:
                        return Path.joinpath(raw_folder_path).joinpath(str(nospace_files[0]))
                        
               

    def find_and_convert_gain(self,rw,header,message):
        #of ispyb_msg
        
        ispyb_msg = Path(message['session_path'])
        

        gain_path = self.find_gain_by_session(ispyb_msg)
        self.log.info("Gain path search was in {}".format(gain_path))
        
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

            

