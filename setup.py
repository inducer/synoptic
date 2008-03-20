#!/usr/bin/env python
# -*- coding: latin1 -*-

def main():
    from setuptools import setup
    import glob
    import os
    import os.path

    setup(name="synoptic",
          version="0.10",
          description="An AJAXy desktop wiki",
          author=u"Andreas Kloeckner",
          author_email="inform@tiker.net",
          license = "BSD, like Python",
          url="http://news.tiker.net/software/synoptic",

          zip_safe=False,

          install_requires=[
              "Paste>=1.6",
              "SqlAlchemy>=0.4.4",
              "SimpleJSON>=1.7",
              ],

          scripts=["bin/synoptic"],
          packages=["synoptic"],
          package_dir={'synoptic': "src"},
          package_data={'synoptic': [
              'static/*.js',
              'static/*.gif',
              'static/*.png',
              'static/*.txt',
              'static/*.css',
              'static/jquery-ui/*.js',
              'static/jquery-ui/themes/flora/*.css',
              'static/jquery-ui/themes/flora/i/*.gif',
              'static/jquery-ui/themes/flora/i/*.png',
              'static/jquery-ui/datepicker/core/*.js',
              'static/jquery-ui/datepicker/core/*.css',
              'static/jquery-ui/datepicker/img/*.gif',
              ]}
         )

if __name__ == "__main__":
    import ez_setup
    ez_setup.use_setuptools()

    main()
