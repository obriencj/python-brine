#! /usr/bin/env python2


"""

author: Christopher O'Brien  <siege@preoccupied.net>

"""


from setuptools import setup, Extension


ext = [ Extension("brine.cellwork", ["brine/cellwork.c"]), ]


setup( name = "brine",
       version = "1.0",
       packages = [ "brine" ],
       test_suite = "tests",
       ext_modules = ext )


#
# The end.
