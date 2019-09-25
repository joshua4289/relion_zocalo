from relion_zo.consumers.zoc_relion_main_consumer import RelionRunner
from relion_zo.consumers.stop_relion_from_ispyb import Relionstop
from relion_zo.consumers.stop_relion_pipeline import Relionsubmitstop
import pytest

def test_check_service_names():
    relion_run = RelionRunner()
    relion_run_name = relion_run.get_name()

    relion_stop = Relionstop()
    relion_stop_name = relion_stop.get_name()


    relion_stop_pipe = Relionsubmitstop()
    relion_stop_pipe = relion_stop_pipe.get_name()

    assert  relion_run_name == "relion.relion_prod_ispyb"
    assert  relion_stop_name == "relion.relion_stop"
    assert  relion_stop_pipe == "relion.relion_stop_pipeline"


