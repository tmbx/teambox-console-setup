#!/usr/bin/python -u

# Note: product versions are represented as two-element lists. Not tuples,
# lists.

import sys, os, getopt
from kfile import *
from krun_compat import *

# Delete the path specified recursively.
def rm_path(path):
    show_cmd_output(["rm", "-rf", path])

class Updater(object):

    def __init__(self):
        
        # Name of the config file.
        self.config_file_name = "config.ini"

        # Location of the directory containing the version-specific update
        # directories. Slash terminated.
        self.version_dir = "updates/"
        
        # Path to the product version file.
        self.product_version_path = "/etc/teambox/product_version"
        
        # Oldest version supported.
        self.oldest_min_version = [1, 2]
        
        # List of update versions, in order.
        self.version_list = None

        # Configuration data obtained from the configuration file.
        self.cfg = None
        
        # Latest version listed in the version directory.
        self.last_version = None
    
    # Parse and return a version number of the form "X.Y". On error, raise an
    # exception containing the message specified.
    def parse_version_number(self, input_str, error_msg="invalid version number"):
        match = re.match("(\d+)\.(\d+)", input_str)
        if not match: raise Exception(error_msg)
        return [int(match.group(1)), int(match.group(2))]
    
    # Read and return the version contained in the file specified.
    def read_version_from_file(self, path):
        f = open(path, "rb")
        line = f.readline().strip()
        f.close()
        return self.parse_version_number(line, "cannot read valid version number from %s" % (path))

    # Fill the update version list.
    def fill_update_version_list(self):
        self.version_list = []
        for file in os.listdir(self.version_dir):
            match = re.match("kas(\d+)\.(\d+)", file)
            if match: self.version_list.append([int(match.group(1)), int(match.group(2))])
        self.version_list.sort()
        if not len(self.version_list): raise Exception("no update version directory found")
    
    # Return the current version of the machine. This function handles legacy
    # products.
    def get_current_version(self):
        # Legacy products.
        for name in [ "kcd", "kwmo", "freemium", "tbxsosd" ]:
            product_path = "/etc/teambox/products/%s/product_version" % (name)
            if os.path.exists(product_path):
                update_version_path = "/etc/teambox/update_version"
                if os.path.exists(update_version_path): return self.read_version_from_file(update_version_path)
                if name == "tbxsosd": return [1, 9]
                return self.read_version_from_file(product_path)
        return self.read_version_from_file("/etc/teambox/product_version")
    
    # Return the version that follows the version specified. Return None if
    # there is no such version.
    def get_next_version(self, version):
        next_index = self.version_list.index(version) + 1
        if next_index == len(self.version_list): return None
        return self.version_list[next_index]

    # Return the path to the directory containing the update script for the
    # version specified. Slash-terminated.
    def get_version_update_dir(self, version):
        return "%skas%d.%d/" % (self.version_dir, version[0], version[1])

    # Parse the source lists from the config file.
    def get_source_list_from_config_file(self, parser):
        self.cfg.old_source_list = []
        old_source_list = parser.items("old_sources")
        old_source_list.sort()
        for i in old_source_list: self.cfg.old_source_list.append(i[1])
        
        self.cfg.source_list = []
        source_list = parser.items("sources")
        source_list.sort()
        for i in source_list: self.cfg.source_list.append(i[1])

    # Parse the config file.
    def parse_config_file(self):
        self.cfg = PropStore()
        parser = read_ini_file(self.config_file_name)
        self.get_source_list_from_config_file(parser)

    # Create the /etc/apt/sources.list with the appropriate sources.
    def create_source_file(self, version):

        # We are at the latest version. Use the latest version sources.
        if version == self.last_version:
            raw_sources = self.cfg.source_list
        
        # Use the old update sources.
        else:
            raw_sources = self.cfg.old_source_list
        
        # Replace 'distrib' by the current version.
        sources = []
        for s in raw_sources: sources.append(s.replace('distrib', "kas%d.%d" % (version[0], version[1])))
        
        # Write the source.list file.
        data = "\n".join(sources) + "\n"
        write_file("/etc/apt/sources.list", data)

    # Print program usage.
    def usage(self, file=sys.stdout):
        file.write("Usage:\n")
        file.write("       %s [options..] [arguments..]\n" % ( sys.argv[0] ))
        file.write("            -l, --last-version    # Update up to <last version>, ignoring other updates.\n")
        file.write("\n")
        try: file.flush()
        except Exception, e: pass
    
    # Switch to maintenance mode.
    def switch_to_maintenance_mode(self, cur_version):
        print("Switching to maintenance mode.")
        if cur_version[0] == 1: show_cmd_output(["kplatshell", "stop"])
        else: show_cmd_output(["kplatshell", "maintenance"])
        print("Now in maintenance mode.")
    
    # Update apt config and cache.
    def update_apt(self, version):
        
        # Update /etc/apt/sources.list.
        self.create_source_file(version)
 
        # Run apt-get update.
        print("Updating /etc/apt/sources.list.")
        show_cmd_output(["apt-get", "--force-yes", "-y", "update"])
    
    # Perform an upgrade of the packages.
    def do_pkg_upgrade(self, cur_version):
        print("Version is current, only upgrading Debian packages.")
        self.switch_to_maintenance_mode(cur_version)
        self.update_apt(cur_version)
        print("Upgrading Debian packages.")
        show_cmd_output(["apt-get", "--force-yes", "-y", "-o", 'DPkg::Options::=--force-confdef', "dist-upgrade"])
    
    # Loop until the current version reaches the last version.
    def do_version_update(self, cur_version):
        first_flag = 1
        while cur_version < self.last_version:
            if not first_flag: print("\n\n")
            first_flag = 0
            
            # Get the next version information.
            next_version = self.get_next_version(cur_version)
            if next_version == None:
                raise Exception("version %d.%d has no next version" % (cur_version[0], cur_version[1]))
            next_version_dir_path = self.get_version_update_dir(next_version)
            
            print("Updating product to version %d.%d." % (next_version[0], next_version[1]))
            
            # Create a new control directory.
            rm_path("ctl")
            os.mkdir("ctl")
            
            # Add 'old_source' file containing the URL where the extra files can
            # be downloaded. This is the URL contained in the first old source
            # provided.
            write_file("ctl/old_source", self.cfg.old_source_list[0].split()[1] + "\n")
            
            # Add a callback file that runs back this script in case an update
            # script needs to take ownership of the update process. This is only
            # done if the next version has itself a next version.
            if self.get_next_version(next_version):
                s = ""
                s += "#!/bin/sh\n"
                s += "cd %s && ./update.py %s\n" % (os.getcwd(), " ".join(sys.argv[1:]))
                write_file("ctl/callback", s)
                show_cmd_output(["chmod", "+x", "ctl/callback"])
             
            # Switch to maintenance mode.
            self.switch_to_maintenance_mode(cur_version)
            
            # Legacy support: write the current version in the update version
            # file for versions below 1.10. At 1.10 we're passing to k2.
            if cur_version < [1,10]:
                write_file("/etc/teambox/update_version", "%d.%d\n" % (cur_version[0], cur_version[1]))
            
            # Update /etc/apt/sources.list.
            self.update_apt(next_version)
            
            # Get the update script arguments. Handle legacy arguments.
            script_cmd = [ "./update.py" ] + sys.argv[1:]
            if cur_version < [1,10]:
                def has_product(name): return os.path.isfile("/etc/teambox/products/%s/product_version" % (name))
                if has_product("kcd"): script_cmd.append("kcd")
                if has_product("kwmo"): script_cmd.append("kwmo")
                if has_product("tbxsosd") or has_product("freemium"): script_cmd.extend(["kps", "freemium"])
            
            # Run the update script.
            print("Running " + " ".join(script_cmd) + ".")
            old_cwd = os.getcwd()
            os.chdir(next_version_dir_path)
            show_cmd_output(script_cmd)
            os.chdir(old_cwd)
            
            # Legacy support: delete the update version file.
            if cur_version < [1,10]: delete_file("/etc/teambox/update_version")
            
            # Reboot requested. Note that 'reboot -f' has to be used here since
            # the reboot scripts fail when we change the base distribution.
            if os.path.isfile("ctl/reboot"):
                print("Rebooting the machine. Your shell may hang up here.")
                sys.stdout.flush()
                sys.stderr.flush()
                show_cmd_output(["reboot", "-f"])
                sys.exit(0)
            
            # Verify that the current version is now the next version.
            cur_version = self.get_current_version()
            if cur_version != next_version:
                raise Exception("the update script did not update the product version correctly")
        
        print("The product is now at the last version.")
            
    # Perform the update.
    def run(self):

        print("\n\nBeginning update process.")
        
        # Parse the configuration file.
        self.parse_config_file()

        try:
            # Parse command line options.
            opts, args = getopt.getopt(sys.argv[1:], "hl:",
                                      ["help", "last-version="])
        except getopt.GetoptError, e:
            sys.stderr.write(str(e) + '\n')
            self.usage(file=sys.stderr)
            sys.exit(2)
        
        # Get options.
        for o, a in opts:
            if o in ('-h', '--help'):
                self.usage()
                sys.exit(0)
            elif o in ('-l', '--last-version'):
                self.last_version = self.parse_version_number(a)

        # Fill the update version list.
        self.fill_update_version_list()
        
        # If the last version hasn't been specified, choose the last one.
        if self.last_version == None: self.last_version = self.version_list[-1]
        
        # Get the current version.
        cur_version = self.get_current_version()

        # Get the current version.
        print "Current version: %d.%d." % (cur_version[0], cur_version[1])
        print "Last version:    %d.%d." % (self.last_version[0], self.last_version[1])

        # Check if we can update.
        if (cur_version < self.oldest_min_version): raise Exception("product is older than last supported version")
        if (cur_version > self.last_version): raise Exception("product is newer than latest update version")
        
        # Special case: the current version is the last version.
        if cur_version == self.last_version: self.do_pkg_upgrade(cur_version)
        
        # We are switching version.
        else: self.do_version_update(cur_version)

def main():
    # Perform the update.
    try: Updater().run()
    except (KeyboardInterrupt, EOFError, SystemExit, Exception), e:
    
        # Raise system exit exceptions.
        if isinstance(e, SystemExit): raise e
         
        # Print errors.
        else:
            sys.stderr.write("Remote update error: " + str(e) + ".\n")
            sys.exit(1)

main()

