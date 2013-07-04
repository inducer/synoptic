#!/usr/bin/env python
# -*- coding: utf-8 -*-


def main():
    from setuptools import setup

    setup(name="synoptic",
          version="2013.1",
          description="An AJAXy notes manager",
          long_description=open("README.rst", "rt").read(),
          author=u"Andreas Kloeckner",
          author_email="inform@tiker.net",
          license="MIT",
          url="http://mathema.tician.de/software/synoptic",
          classifiers=[
              'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Environment :: Web Environment',
              'Intended Audience :: End Users/Desktop',
              'Intended Audience :: Developers',
              'Intended Audience :: Science/Research',
              'Intended Audience :: Legal Industry',
              'License :: OSI Approved :: MIT License',
              'Operating System :: MacOS :: MacOS X',
              'Operating System :: Microsoft :: Windows',
              'Operating System :: POSIX',
              'Programming Language :: Python',
              'Topic :: Communications :: Email',
              'Topic :: Office/Business',
              'Topic :: Utilities',
              'Topic :: Text Processing',
              ],
          zip_safe=False,

          install_requires=[
              "Paste>=1.7",
              "SQLAlchemy>=0.6.6",
              "sqlalchemy-migrate>=0.6.1",
              "SimpleJSON>=1.7",
              "parsedatetime>=0.8.6",
              "ipaddr",
              ],

          scripts=["bin/synoptic"],
          packages=[
                  "synoptic",
                  "synoptic.schema_ver_repo",
                  "synoptic.schema_ver_repo.versions"
                  ],
          include_package_data=True,
          package_data={
                  'synoptic': [
                      'static/*.js',
                      'static/*.gif',
                      'static/*.png',
                      'static/*.txt',
                      'static/*.css',
                      'static/jquery-ui/*.js',
                      'static/jquery-ui-css/smoothness/*.css',
                      'static/jquery-ui-css/smoothness/images/*.png',
                      ],
                  "synoptic.schema_ver_repo": ["migrate.cfg"],
              }
          )

if __name__ == "__main__":
    main()
