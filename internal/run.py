#!/usr/bin/python

import sys, os, getopt
import kprompt
from kfile import *
from krun import *

# Name of the config file.
stock_config_file_name = "config.ini.stock"
config_file_name = "config.ini"

# Get a config object. Parse config.ini if present. Otherwise, parse
# config.ini.stock if present.
def get_config_object():
    cfg = PropStore()
    cfg.ip = None
    cfg.script_name = None
    cfg.script_arg = ''
    cfg.delete_paths = None
    cfg.ask_confirm = 1
    cfg.source_list = []
    cfg.old_source_list = []
    cfg.tunnel_list = []

    parser = None
    if os.path.isfile(config_file_name):
        parser = read_ini_file(config_file_name)
    elif os.path.isfile(stock_config_file_name):
        parser = read_ini_file(stock_config_file_name)

    if parser:
        cfg.ip = parser.get("config", "ip")
        cfg.script_name = parser.get("config", "script_name")
        cfg.script_arg = parser.get("config", "script_arg")
        cfg.delete_paths = parser.get("config", "delete_paths")
        cfg.ask_confirm = parser.get("config", "ask_confirm")
        
        source_list = parser.items("sources")
        source_list.sort()
        for i in source_list: cfg.source_list.append(i[1])

        old_source_list = parser.items("old_sources")
        old_source_list.sort()
        for i in old_source_list: cfg.old_source_list.append(i[1])
        
        tunnel_list = parser.items("tunnels") 
        tunnel_list.sort()
        for i in tunnel_list:
            tunnel = i[1]
            if not re.match("^\d+:[a-zA-Z0-9._-]+:\d+$", tunnel): raise Exception("invalid tunnel '%s'" % (tunnel))
            cfg.tunnel_list.append(tunnel)
        
    return cfg

# Return the name of the current directory.
def get_cur_dir_name():
    return os.path.basename(os.getcwd())

# Create the sources.list file locally.
def create_source_file(source_list):
    data = "\n".join(source_list) + "\n"
    write_file("sources.list", data)

# Delete the target host paths specified.
def delete_remote_paths(ip, paths):
    show_cmd_output(["ssh", "root@" + ip, "rm -rf " + paths])

# Copy the content of the current directory to the target host.
def upload_cur_dir(ip):
    show_cmd_output(["scp", "-r", "../" + get_cur_dir_name(), "root@" + ip + ":/"])

# Establish the tunnel specified.
def establish_tunnel(ip, tunnel):
    show_cmd_output(["ssh", "-R", tunnel, "-N", "root@" + ip, "&"], shell_flag=1)

# Run the setup script on the target host.
def run_setup_script(ip, script_name, script_arg):
    show_cmd_output(["ssh", "root@" + ip,
                     "cd " + "/" + get_cur_dir_name() + " && ./" + script_name + " " + script_arg])

# Ask the confirmation to proceed.
def ask_confirm(cfg):
    
    # Get the last update version if the updates directory exist.
    version_dir = "updates/"
    last_version = None
    if os.path.isdir(version_dir):
        version_list = []
        for file in os.listdir(version_dir):
            match = re.match("kas(\d+)\.(\d+)", file)
            if match: version_list.append([int(match.group(1)), int(match.group(2))])
        version_list.sort()
        if len(version_list): last_version = version_list[-1]

    s = ""
    s += "===============================================================================\n"
    s += "Host:          " + cfg.ip + "\n"
    s += "Directory:     " + get_cur_dir_name() + "\n"
    if cfg.delete_paths: s += "Delete:        " + cfg.delete_paths + "\n"
    s += "Command:       " + cfg.script_name + " " + cfg.script_arg + "\n"
    for i in cfg.source_list: s += "Source:        " + i + "\n"
    for i in cfg.old_source_list: s += "Old source:    " + i + "\n"
    for i in cfg.tunnel_list: s += "Tunnel:        " + i + "\n"
    if last_version: s += "Last version:  kas%i.%i\n" % (last_version[0], last_version[1])
    s += "===============================================================================\n\n"
    sys.stdout.write(s)
    
    return kprompt.get_confirm("Proceed?")

# Print the usage to a file object (default file object is stdout).
def usage(file=sys.stdout):
    file.write("Usage:\n")
    file.write("       %s [arguments..]\n" % ( sys.argv[0] ))
    file.write("            -h, --help                              # Show this help.\n")
    file.write("            -i, --ip <ip>                           # Set the IP of the remove server.\n")
    file.write("            -s, --script <script name>              # Set the script to use.\n")
    file.write("            -a, --scripts-args <script arguments>   # Set the script arguments to use.\n")
    file.write("            -c, --confirm                           # Ask for a confirmtion before\n")
    file.write("                                                    # proceeding.\n")
    file.write("            -j, --no-confirm                        # Don't ask for a confirmation.\n")
    file.write("            -d, --delete-paths <paths>              # Delete paths remotely.\n")
    file.write("            -u, --source <source>                   # Append a source for a new install or\n")
    file.write("                                                    # the last update.\n")
    file.write("            -o, --old-source <source>               # Append a source for old updates.\n")
    file.write("            -t, --tunnel <tunnel>                   # Append a tunnel.\n")
    file.write("\n")
    file.flush()
    try: file.flush()
    except Exception, e: pass
    
def main():
    try:
        cfg = get_config_object()

        try:
            # Parse command line options.
            opts, args = getopt.getopt(sys.argv[1:], "hi:s:a:cjd:u:o:t:", 
                                       ["help", "ip=", "script=", "script-args=", "confirm", 
                                        "no-confirm", "delete-paths=", "source=", "old-source=", "tunnel="])
        except getopt.GetoptError, e:
            sys.stderr.write(str(e) + '\n')
            usage(file=sys.stderr)
            sys.exit(2)

        # Update config object with command line options.
        for o, a in opts:
            if o in ("-h", "--help"):
                usage()
                sys.exit(0)
            elif o in ("-i", "--ip"):
                cfg.ip = a
            elif o in ("-s", "--script"):
                cfg.script_name = a
            elif o in ("-a", "--script-args"):
                cfg.script_arg = a
            elif o in ("-c", "--confirm"):
                cfg.ask_confirm = True
            elif o in ("-j", "--no-confirm"):
                cfg.ask_confirm = False
            elif o in ("-d", "--delete-paths"):
                cfg.delete_paths = a
            elif o in ("-u", "--source"):
                cfg.source_list += [a]
            elif o in ("-o", "--old-source"):
                cfg.old_source_list += [a]
            elif o in ("-t", "--tunnel"):
                cfg.tunnel_list += [a]
            else:
                sys.stderr.write("Bad option.\n")
                usage(file=sys.stderr)
                sys.exit(2)

        # Append remaining arguments to the script arguments.
        cfg.script_arg += ' ' + ' '.join(args)

        # Validate options.
        if not cfg.ip or cfg.ip == '': raise Exception("no IP specified")
        if not cfg.script_name or cfg.script_name == '': raise Exception("no script name specified")

        ip = cfg.ip
        
        if cfg.ask_confirm and not ask_confirm(cfg): return

        sys.stdout.write("Starting setup of " + ip + ".\n")
        
        for i in cfg.tunnel_list:
            sys.stdout.write("Establishing tunnel %s.\n" % (i))
            establish_tunnel(ip, i)
        
        if cfg.delete_paths:
            sys.stdout.write("Deleting " + cfg.delete_paths + "\n")
            delete_remote_paths(ip, cfg.delete_paths)
        
        sys.stdout.write("Creating sources.list file.\n")
        create_source_file(cfg.source_list)
        
        sys.stdout.write("Uploading '%s' directory.\n" % (get_cur_dir_name()))
        upload_cur_dir(ip)
        
        sys.stdout.write("Executing '" + cfg.script_name + " " + cfg.script_arg + "'.\n")
        run_setup_script(ip, cfg.script_name, cfg.script_arg)
        
    except (KeyboardInterrupt, EOFError, SystemExit, Exception), e:
    
        # Raise system exit exceptions.
        if isinstance(e, SystemExit): raise e
        
        # Ignore interruptions.
        elif isinstance(e, KeyboardInterrupt) or isinstance(e, EOFError): return
         
        # Print errors.
        else:
            sys.stderr.write("Error: " + str(e) + ".\n")
            sys.exit(1)
     
    # Delete the sources.list file, if it exists.
    finally:
        try: delete_file("sources.list")
        except: pass
    
main()

