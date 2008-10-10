"""

author: Christopher O'Brien  <siege@preoccupied.net>

$Revision: 1.3 $ $Date: 2007/11/02 18:52:27 $

"""


from distutils.core import setup
from distutils.extension import Extension


ext = [ Extension("brine.cellwork", ["src/cellwork.c"]), ]


setup( name = "brine",
       version = "1.0",
       package_dir = {"brine": "src"},
       packages = ["brine", "brine.tests"],
       ext_modules = ext )


#
# The end.
