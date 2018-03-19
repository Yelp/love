# -*- coding: utf-8 -*-
import yaml


_offices = yaml.safe_load(open('offices.yaml'))
OFFICES = set(_offices['Offices'])
