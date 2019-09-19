from __future__ import absolute_import, division, print_function
from workflows.services.common_service import CommonService
import workflows.recipe


class Relionstop(CommonService):
    '''A zocalo service for to stop Relion from IsPyB '''

    # Human readable service name
    _service_name = "relion.relion_stop"

    # Logger name
    _logger_name = 'relion.zocalo.services.runner'

    def initializing(self):
        """Subscribe to the per_image_analysis queue. Received messages must be acknowledged.

                """

        queue_name = "relion.relion_stop"
        self.log.info("queue that is being listened to is %s" % queue_name)
        workflows.recipe.wrap_subscribe(self._transport, queue_name,
                                        self.stop_relion, acknowledgement=True, log_extender=self.extend_log,
                                        allow_non_recipe_messages=True)

    def stop_relion(self, rw, header, message):
        self.log.info("Stop relion through zocalo")
        import os
        try:
            from pathlib2 import Path
        except:
            from pathlib import Path

        ispyb_msg = message['session_path']

        ispyb_msg_path = Path(ispyb_msg)

        import os
        import re
        import sys

        # the regular expression covers all cases of RUNNING_*

        session_path = ispyb_msg_path.parents[2]
        session_name = session_path.name

        relion_project_dir = Path.joinpath(session_path).joinpath(
            'processed').joinpath('relion_' + session_name)
        self.log.info(relion_project_dir)

        run_files = [f for f in os.listdir(
            str(relion_project_dir)) if re.match(r'RUNNING*', f)]

        self.log.info("%s has asked to be stopped" % (str(session_path)))

        if run_files:
        for r in run_files:
            file_to_delete = session_path.joinpath(
                relion_project_dir).joinpath(r)

            if file_to_delete.exists():
                self.log.info("%s will be removed " % (file_to_delete))
                try:
                    os.remove(str(file_to_delete))
                except:
                    self.log.info(
                        "Nothing to delete %s has been deleted " % file_to_delete)

        # acknowledge in both cases whether file was deleted or if it doesn't exist
        self.transport.ack(header)
