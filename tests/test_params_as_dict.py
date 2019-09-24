#!/usr/bin/env python

#from relion_zo.consumers.zoc_relion_main_consumer import RelionRunner
import pytest

from relion_zo.consumers.zoc_relion_main_consumer import RelionRunner
#TODO:find out how to make a fixture because file does not always exist check artifacts




def test_user_input():
    r = RelionRunner()
    json_user_params = r.params_as_dict(user_ip='/dls/tmp/jtq89441/dls/m02/data/2019/em12345-01/.ispyb/processing/relion_msg.json')
    print(json_user_params)


# check for extension of raw and gain images

    assert 'import_images' in json_user_params
    extension = json_user_params['import_images'].split('/*')[-1]
    supported_extensions = ['.mrc','.tif','.tiff']

    def test_raise_on_dm4(ext):
        if str(ext) == '.dm4':
            raise ValueError('.dm4 is not in supported extensions list ')


    def test_raise_on_bool_is_str(opt):
        if isinstance(opt,basestring):
            raise ValueError('expected boolean from ispyb dispatch got {}'.format(type(opt)))


       


        with pytest.raises(ValueError):
            test_raise_on_dm4('.dm4')
            assert '.dm4' not in supported_extensions
            assert extension in supported_extensions

    if getattr(json_user_params,'gain_image',''):
        gain_extension = json_user_params['gain_image'].split('/*')[-1]

        if gain_extension:
            assert gain_extension in supported_extensions