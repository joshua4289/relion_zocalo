#!/usr/bin/env python

#from relion_zo.consumers.zoc_relion_main_consumer import RelionRunner
import pytest
from relion_zo.consumers.zoc_relion_main_consumer import RelionRunner
import json


#TODO:find out how to make a fixture because file does not always exist check artifacts


@pytest.fixture
def sample_data():
    #php_to_python = {true:True,false:False}
    true = True
    false = False  
    
    sample_data = {
    "import_images": "/dls/tmp/jtq89441/dls/m02/data/2019/em12345-01/raw/GridSquare_*/Data/*.mrc",
    "motioncor_gainreference": "/dls/tmp/jtq89441/dls/m02/data/2019/em122345-01/raw/Gain.mrc",
    "voltage": 200,
    "Cs": 2.7,
    "ctffind_do_phaseshift": true ,
    "angpix": 1.0,
    "motioncor_doseperframe": 0.5,
    "stop_after_ctf_estimation": false,
    "do_class2d": true,
    "do_class3d": true,
    "autopick_LoG_diam_max": 10,
    "autopick_LoG_diam_min": 100,
    "mask_diameter": 190,
    "extract_downscale": true,
    "extract_boxsize": 256,
    "extract_small_boxsize": 64,
    "do_second_pass": true,
    "do_class2d_pass2": true,
    "do_class3d_pass2": true,
    "autopick_do_cryolo": true
    
    }

    
    return sample_data


def test_user_input(sample_data):
    ''' testing the user input not the relion-it methods '''        
    r = RelionRunner()
    json_user_params = sample_data 
    
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


 
def test_box_size_only_even(sample_data):
    
    """ relion and EM programs in general hate odd box sizes """     
    
    assert sample_data['extract_boxsize'] % 2 == 0
    assert sample_data['extract_small_boxsize'] % 2 == 0
