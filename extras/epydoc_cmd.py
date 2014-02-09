# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, see
# <http://www.gnu.org/licenses/>.


from setuptools import Command


class EpydocCommand(Command):


    user_options = []


    def initialize_options(self):
        pass


    def finalize_options(self):
        pass


    def has_epydoc(self):
        try:
            import epydoc.cli
        except ImportError:
            return False
        else:
            return True


    def run_epydoc(self):
        import epydoc.cli
        from os.path import join

        self.announce("%r" % epydoc.cli)


    def run(self):
        if not self.has_epydoc():
            self.warn("epydoc not present")
            return

        self.run_command("build")
        self.run_epydoc()


#
# The end.
