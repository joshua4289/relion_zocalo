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
    print(Path.__module__)


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
                print (f'type is {type(nospace_files)}')
                #print('length of the list is ')
                #make no_space  a list by list(iter)
                # because the paths generated will be changing dependent on 
                # what is exposed to the __next__ method call
                #  if length == 1 return else return from the base of the list 
                #of files
                
                if not nospace_files:
                    return None
                    
                for f in nospace_files:
                    if len(nospace_files) == 1:
                        return Path.joinpath(raw_folder_path).joinpath(f)
                    else:
                        return Path.joinpath(raw_folder_path).joinpath(str(nospace_files[0]))
                        
                # try:
                #     nospace_file =              #next(nospace_files) #next(nospace_files)
                #     self.log.info(f'returning Path withim the function{nospace_file}')
                #     yield (nospace_file) #Path.joinpath(raw_folder_path).joinpath(str(nospace_file))

                # except StopIteration:
                #     self.log.info('stop iteration reached ')
                #     return None

                # if len(list(nospace_files > 1 )):
                #     return Path.joinpath(raw_folder_path).joinpath(str(list(nospace_files).pop)) 

                # else:
                # self.log.info('No relevant gain files found..continuing without Gain ')
                # return  None

                # if len(list(files)) > 0 :
                #     """ iterate over the files list if space continue else return """

                #     print(f'this is the list of files{list(files)}')    
                    # files_accepted = map(no_space,files)                    
                    # print(list(files))
                    # print(f'files accepted are {files_accepted}')

                    #print(list(files_accepted))
                    
                    # for f in files:
                    
                    #     #file_without_spaces = self.skip_path_with_spaces()
                    #     file_without_spaces = [ Path(f) no_space(PurePath.name(f))]
                    #     print(f'file without spaces is {file_without_spaces}')    

                        
                    #     if len(file_without_spaces) > 0:
                    #         try:
                    #             print(f'path found was {file_without_spaces}')
                    #             return Path.joinpath(raw_folder_path).joinpath(str(f))  #joinpath(str(next(files))) 
                    #         except StopIteration:
                    #             print("list does not contain valid entries ")
                    #             pass     
                    #     else:
                    #         self.log.info("file had spaces in it this is not suported")
                    
                    # for f in files:
                    #     if self.skip_path_with_spaces(f):
                    #         print('file had spaces in it not suported')
                    #         continue
                        
                    # return Path.joinpath(raw_folder_path).joinpath(str(next(files)))    
                    
                    # print('No gain was found in {}'.format(raw_folder_path))
                    # continue
                    #(str(files[-1]))

    def find_and_convert_gain(self,rw,header,message):
        #of ispyb_msg
        
        ispyb_msg = Path(message['session_path'])
        #ispyb_msg= Path("/dls/tmp/jtq89441/dls/m02/data/2019/em12345-01/.ispyb/processed/ispyb_msg.json")

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

            

