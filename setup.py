from __future__ import absolute_import
#!/usr/bin/env python
# -*- coding: utf-8 -*-


def main():
    import sys

    extra_requires = []
    if sys.version_info < (3,):
        extra_requires += ["ipaddress"]

    from setuptools import setup, find_packages

    setup(name="synoptic",
          version="2016.1",
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
              'Programming Language :: Python :: 2.6',
              'Programming Language :: Python :: 2.7',
              # paste is not there yet, apparently
              #'Programming Language :: Python :: 3.4',
              #'Programming Language :: Python :: 3.5',
              'Programming Language :: Python',
              'Topic :: Communications :: Email',
              'Topic :: Office/Business',
              'Topic :: Utilities',
              'Topic :: Text Processing',
              ],
          zip_safe=False,

          install_requires=extra_requires + [
              "Paste>=2",
              "SQLAlchemy>=0.8",
              "sqlalchemy-migrate>=0.7.2.24",
              "parsedatetime>=0.8.6",
              "pytools>=2014.3.5",
              "six",
              ],

          scripts=["bin/synoptic"],
          packages=find_packages(),
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
