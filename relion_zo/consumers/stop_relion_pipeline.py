from __future__ import absolute_import, division, print_function
from workflows.services.common_service import CommonService
import workflows.recipe



class Relionsubmitstop(CommonService):
    '''A zocalo service for to stop Relion RELION_SUBMITTED_JOBS and RUNNING_* for relion from IsPyB '''

    # Human readable service name
    _service_name = "relion.reset"

    # Logger name
    _logger_name = 'relion.zocalo.services.runner'

    def initializing(self):
        """Subscribe to the per_image_analysis queue. Received messages must be acknowledged.

		"""

        queue_name = "relion.reset"
        self.log.info("queue that is being listened to is %s" % queue_name)
        workflows.recipe.wrap_subscribe(self._transport, queue_name,
                                        self.stop_relion, acknowledgement=True, log_extender=self.extend_log,
                                        allow_non_recipe_messages=True)



    def stop_relion(self, rw, header, message):
        self.log.info("relion RESET through zocalo")

        import os
        import re
        import sys
        
        if sys.version_info[0] > 2:
            from pathlib import Path
        
        else:
            from pathlib2 import Path
    

        session_path  = Path(message['session_path'])
        session_name = session_path.name
        relion_project_dir = Path.joinpath(session_path).joinpath('processed').joinpath('relion_' + session_name)


        relion_jobs_file = Path.joinpath(relion_project_dir).joinpath('RELION_IT_SUBMITTED_JOBS')
        ispyb_jobs_file = Path.joinpath(session_path).joinpath('.ispyb/processed/RELION_IT_SUBMITTED_JOBS')

        #start the remove only both exists this maybe opens you to timing issues needs improvement
        #remove from both dirs

        if relion_jobs_file and ispyb_jobs_file:
            try:
                os.remove(str(relion_jobs_file))
                self.log.info("{} submitted jobs file was removed ".format(relion_jobs_file))
                os.remove(str(ispyb_msg_path))
                self.log.info("{} submitted jobs file was removed ".format(ispyb_jobs_file))

            except:
                self.log.info("file {} not found".format(relion_jobs_file))
                self.log.info("file {} not found".format(ispyb_jobs_file))

        run_files = [f for f in os.listdir(str(relion_project_dir)) if re.match(r'RUNNING*', f)]


        self.log.info("%s has asked to be stopped" % (str(session_path)))

        for r in run_files:
            file_to_delete = session_path.joinpath('processed').joinpath(relion_project_dir).joinpath(r)
            file_to_delete_ispyb = session_path.joinpath('.ispyb').joinpath('processed').joinpath(r)

            if file_to_delete.exists:
                self.log.info("%s will be removed " % (file_to_delete))
                self.log.info("%s ispyb file will be removed " % (file_to_delete_ispyb))

                try:
                    os.remove(str(file_to_delete))
                    os.remove(str(file_to_delete_ispyb))


                except:
                    self.log.info("Nothing to delete %s has been deleted " % file_to_delete)


        #in both cases ack
        self.transport.ack(header)

