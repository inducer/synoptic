#!/usr/bin/env python
# -*- coding: latin1 -*-

def main():
    from setuptools import setup
    import glob
    import os
    import os.path

    setup(name="synoptic",
          version="0.90",
          description="An AJAXy notes manager",
          long_description="""
          Synoptic is "GMail for your notes". It gives you an efficient and
          friendly interface that makes it possible to keep and categorize a
          *large* number of small-ish notes and tidbits of information.

          The following features set it apart:

          * **Fully versioned:** Never deletes *anything*, *ever*. If you want
            to go back to a previous version of something, just drag the
            slider up there in the top-left corner.

          * **Efficient keyboard control.** Never take your hands of the
            keyboard while you're working with Synoptic. All every-day
            functions are keyboard-accessible.

          * **Tags.** Synoptic is meant to scale to *large* note collections.
            Tags provide easy categorization, plus the Web 2.0 goodness of that
            tag cloud over there on the left.

          * **Easy Syntax.** Synoptic uses
            Markdown to allow you to type formatted notes easily and quickly.
          """,
          author=u"Andreas Kloeckner",
          author_email="inform@tiker.net",
          license = "MIT",
          url="http://news.tiker.net/software/synoptic",
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
              "Paste>=1.6",
              "SqlAlchemy>=0.4.4",
              "SimpleJSON>=1.7",
              "parsedatetime>=0.8.4",
              ],

          scripts=["bin/synoptic"],
          packages=["synoptic"],
          package_dir={'synoptic': "src"},
          include_package_data=True,
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
