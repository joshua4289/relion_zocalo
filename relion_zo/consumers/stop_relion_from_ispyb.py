from __future__ import absolute_import, division, print_function
from workflows.services.common_service import CommonService
import workflows.recipe


class Relionstop(CommonService):
    '''A zocalo service for to stop Relion from IsPyB '''

    # Human readable service name
    _service_name = "relion.stop"

    # Logger name
    _logger_name = 'relion.zocalo.services.runner'

    def initializing(self):
        """Subscribe to the per_image_analysis queue. Received messages must be acknowledged.

                """

        queue_name = "relion.stop"
        self.log.info("queue that is being listened to is %s" % queue_name)
        workflows.recipe.wrap_subscribe(self._transport, queue_name,
                                        self.stop_relion, acknowledgement=True, log_extender=self.extend_log,
                                        allow_non_recipe_messages=True)

    def stop_relion(self, rw, header, message):
        self.log.info("Stop relion through zocalo")

        import os
        import re
        import sys
        
        if sys.version_info[0] > 2:
            from pathlib import Path
        
        else:
            from pathlib2 import Path

        #ispyb_msg = message['session_path']

        #ispyb_msg_path = Path(ispyb_msg)
        
        #implementation-choice:
        #-----------------------
        #Changed the messages that ispyb gives will be of the session
        #for the stop events this is because the front-end needs to simply 
        # send a zocalo messsage that needs to be consumed 
        # there is seemingly no benifit to logging stop mesaages on 
        # the file-system as tracked by greylog

        session_path = Path(message['session_path'])
        session_name = session_path.name

        relion_project_dir = Path.joinpath(session_path).joinpath('processed').joinpath('relion_' + session_name)

        run_files = [f for f in os.listdir(str(relion_project_dir)) if re.match(r'RUNNING*', f)]

        self.log.info("%s has asked to be stopped" % (str(session_path)))


        if run_files:
            for r in run_files:
                file_to_delete = session_path.joinpath(
                    relion_project_dir).joinpath(r)
                file_to_delete_ispyb = session_path.joinpath('.ispyb').joinpath('processed').joinpath(r)

                if file_to_delete.exists():
                    self.log.info("%s will be removed " % (file_to_delete))
                    self.log.info("%s ispyb file will be removed " % (file_to_delete_ispyb))
                    try:
                        os.remove(str(file_to_delete))
                        os.remove(str(file_to_delete_ispyb))
                    except:
                        self.log.info(
                            "Nothing to delete %s has been deleted " % file_to_delete)

        else:
            self.log.info("No instances of relion-it running for {}".format(session_path))

        # acknowledge in both cases whether file was deleted or if it doesn't exist

        self.transport.ack(header)
