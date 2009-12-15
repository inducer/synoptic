#!/usr/bin/env python
# -*- coding: latin1 -*-

def main():
    from setuptools import setup
    import glob
    import os
    import os.path

    setup(name="synoptic",
          version="0.92.1",
          description="An AJAXy notes manager",
          long_description="""
          Synoptic is "GMail for your notes". It gives you an efficient and friendly
          interface that makes it possible to keep and categorize a *large* number of
          small-ish notes and tidbits of information.

          The following features set it apart:

          * **Fully versioned.** Never deletes *anything*, *ever*. If you want to go back
            to a previous version of something, just drag that slider up there in the
            top-left corner.

          * **Super-simple Navigation.** Adaptive tag clouds, 
            support for the forward/back button on your browser, 
            query links, support for browser bookmarks. All to make sure
            you can find that note when you need it.

          * **Powerful searching.** Synoptic is meant to keep *large*
            note collections manageable and accessible. You can search for items
            based on tags, their creation time, or even search through their *full text*. 
            Plus arbitrary logical combinations of them, using the 
            logical operatos and, or, and not.

          * **Easy Markup.** Synoptic uses
            Markdown to allow you to type formatted notes easily and
            quickly. Plus, there are a few extensions to facilitate
            typing math.

          * **Advanced Features.** A lot of refinement work has gone into
            making Synoptic work as seamlessly as possible. You may never notice
            many of these refinements, because they're meant to make stuff work like
            it's supposed to.
          """,
          author=u"Andreas Kloeckner",
          author_email="inform@tiker.net",
          license = "MIT",
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
              "SqlAlchemy>=0.5.1",
              "SimpleJSON>=1.7",
              "parsedatetime==0.8.6",
              "ipaddr",
              ],

          scripts=["bin/synoptic"],
          packages=["synoptic"],
          include_package_data=True,
          package_data={'synoptic': [
              'static/*.js',
              'static/*.gif',
              'static/*.png',
              'static/*.txt',
              'static/*.css',
              'static/jquery-ui/*.js',
              'static/jquery-ui/themes/base/*.css',
              'static/jquery-ui/themes/base/images/*.png',
              ]}
         )

if __name__ == "__main__":
    import distribute_setup
    distribute_setup.use_setuptools()

    main()
