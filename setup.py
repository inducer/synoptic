#!/usr/bin/env python
# -*- coding: latin1 -*-

from distutils.core import setup,Extension
import glob
import os
import os.path

setup(name="synoptic",
      version="0.10",
      description="An AJAXy desktop wiki",
      author=u"Andreas Kloeckner",
      scripts=["bin/synoptic"],
      author_email="inform@tiker.net",
      license = "BSD, like Python",
      url="http://news.tiker.net/software/synoptic",
      packages=["synoptic"],
      package_dir={"synoptic": "src"},
      package_data={'synoptic': ['static/*']}
     )
