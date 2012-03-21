#!/usr/bin/env python

import getpass, getopt, syslog
from kprompt import *
from kasmodel import *

# Platform shell class.
class PlatShell:
    def __init__(self):
        
        # Instance of the service manager.
        self.service_manager = ServiceManager()
        
        # Instance of the root configuration node.
        self.config = RootConfigNode()
        
        # Standard output stream. Only the 'write' method is supported.
        self.stdout = sys.stdout
        
        # Standard error stream. Only the 'write' method is supported.
        self.stderr = sys.stderr
        
        # True if the commands run must be echo'ed.
        self.echo_cmd_flag = 0
        
        # Trapped exception list.
        self.trapped_exception_list = (KeyboardInterrupt, EOFError, SystemExit, Exception)
        
        # Help strings.
        self.global_help_str = \
            "Teambox platform shell.\n" +\
            "\n" +\
            "Commands:\n" +\
            "  help               Show help about a command.\n" +\
            "  info               Show the configuration summary.\n" +\
            "  health             Show the server health status.\n" +\
            "  ifconfig           Show the status of the network interfaces.\n" +\
            "  netstat            Show the addresses and ports being listened to.\n" +\
            "  services           Show the status of the services.\n" +\
            "  setup              Change the basic configuration.\n" +\
            "  production         Switch to production mode.\n" +\
            "  maintenance        Switch to maintenance mode.\n" +\
            "  update             Update the machine.\n" +\
            "  enable             Enable the specified service.\n" +\
            "  disable            Disable the specified service.\n" +\
            "  start              Start the specified services.\n" +\
            "  stop               Stop the specified services.\n" +\
            "  set-host           Set the fully qualifed host name.\n" +\
            "  set-root-pwd       Set the UNIX root account password.\n" +\
            "  set-admin-pwd      Set the administration password.\n" +\
            "  write-service-cfg  Update the service configuration.\n" +\
            "  write-network-cfg  Update the network configuration.\n" +\
            "  write-issue        Update the content of /etc/issue.\n" +\
            "  restart-services   Restart the Teambox services.\n" +\
            "  restart-network    Restart the network interfaces.\n" +\
            "\n" +\
            "Global options:\n" +\
            "  -h, --help [cmd]     Print help and exit.\n" +\
            "  -s, --syslog         Log output to syslog.\n" +\
            "  -e, --echo           Echo the name of every command run.\n"

        self.help_help_str = \
            "help [command]\n" +\
            "\n" +\
            "Show help about a command, or list the commands supported.\n"

        self.info_help_str = \
            "info\n" +\
            "\n" +\
            "Show the configuration summary, including the server health and the enabled\n" +\
            "user services.\n"
        
        self.health_help_str = \
            "health\n" +\
            "\n" +\
            "Show the server health status. The first error detected is displayed.\n"
         
        self.ifconfig_help_str = \
            "ifconfig\n" +\
            "\n" +\
            "Display the stripped output of 'ifconfig -a'.\n"

        self.netstat_help_str = \
            "netstat\n" +\
            "\n" +\
            "Display the stripped output of 'netstat -nltp'.\n"
            
        self.services_help_str = \
            "services\n" +\
            "\n" +\
            "Show the status of all services.\n"
        
        self.setup_help_str = \
            "setup\n" +\
            "\n" +\
            "Run the wizard to change the basic configuration of the machine.\n"
        
        self.production_help_str = \
            "production\n" +\
            "\n" +\
            "Switch to production mode. All enabled services are started and remote database\n" +\
            "access to the machine is allowed.\n"

        self.maintenance_help_str = \
            "maintenance\n" +\
            "\n" +\
            "Switch to maintenance mode. All non-essential services are stopped and remote\n" +\
            "database access to the machine is disabled.\n"
        
        self.update_help_str = \
            "update\n" +\
            "\n" +\
            "Update the software of the machine. The machine is put in maintenance mode.\n" +\
            "It must be put back in production mode manually once all the machines in the\n" +\
            "server pool have been updated.\n"
        
        self.enable_help_str = \
            "enable [-f,--force] <service>\n" +\
            "\n" +\
            "Mark the service specified as enabled. Nothing is done if the service is not\n" +\
            "present or cannot be enabled. No attempt is made to start the service. If\n" +\
            " --force is specified, the service is enabled even if it seems to be already\n" +\
            "enabled.\n"

        self.disable_help_str = \
            "disable [-f,--force] <service>\n" +\
            "\n" +\
            "Mark the service specified as disabled. Nothing is done if the service is not\n" +\
            "present or cannot be disabled. No attempt is made to stop the service. If\n" +\
            " --force is specified, the service is disabled even if it seems to be already\n" +\
            "disabled.\n"

        self.start_help_str = \
            "start [-f,--force] [service1, service2, ...]\n" +\
            "\n" +\
            "Start the services specified. If no service is specified, all configured\n" +\
            "services are started. If --force is specified, the start-up scripts are invoked\n" +\
            "even if the services seem to be running.\n"

        self.stop_help_str = \
            "stop [-f,--force] [service1, service2, ...]\n" +\
            "\n" +\
            "Stop the services specified. If no service is specified, all services are\n" +\
            "stopped. If --force is specified, the start-up scripts are invoked even if the\n" +\
            "services seem to be stopped.\n"

        self.set_host_help_str = \
            "set-host <name>\n" +\
            "\n" +\
            "Set the fully qualified host name.\n"

        self.set_root_pwd_help_str = \
            "set-root-pwd <password>\n" +\
            "\n" +\
            "Set the UNIX root account password.\n"
        
        self.set_admin_pwd_help_str = \
            "set-admin-pwd <password>\n" +\
            "\n" +\
            "Set the administration password used by the Teambox services. Postgres must\n" +\
            "be running for that command to succeed.\n"
        
        self.write_service_cfg_help_str = \
            "write-service-config\n" +\
            "\n" +\
            "Update the configuration files of the Teambox services. The services are\n" +\
            "not restarted. The configuration is normalized prior to being written.\n"

        self.write_network_cfg_help_str = \
            "write-network-cfg\n" +\
            "\n" +\
            "Update the network configurition files. The network interfaces are not\n" +\
            "restarted.\n"

        self.write_issue_help_str = \
            "write-issue\n" +\
            "\n" +\
            "Update the '/etc/issue' file with the configuration information.\n"

        self.restart_services_help_str = \
            "restart-services\n" +\
            "\n" +\
            "Stop all non-essential or disabled services then start all enabled services. The\n" +\
            "service configuration files are updated.\n"
        
        self.restart_network_help_str = \
            "restart-network\n" +\
            "\n" +\
            "Reload the hostname and the firewall rules, and restart the network interfaces.\n" +\
            "The network configuration files are updated.\n"
        
        # Command dispatch table. The first column is the command name, the
        # second is the number of arguments, the third is the short options
        # accepted, the fourth is the long options accepted, the fifth is the
        # handler function to call, the sixth is the help string. 'None' can be
        # specified for the number of arguments when the command takes a
        # variable number of arguments. The arguments supplied to the handler
        # are the values returned by getopt().
        self.cmd_dispatch_table = \
            (("help", None, "", [], self.handle_help, self.help_help_str),
             ("info", 0, "", [], self.handle_info, self.info_help_str),
             ("health", 0, "", [], self.handle_health, self.health_help_str),
             ("ifconfig", 0, "", [], self.handle_ifconfig, self.ifconfig_help_str),
             ("netstat", 0, "", [], self.handle_netstat, self.netstat_help_str),
             ("services", 0, "", [], self.handle_services, self.services_help_str),
             ("setup", 0, "", [], self.handle_setup, self.setup_help_str),
             ("production", 0, "", [], self.handle_production, self.production_help_str),
             ("maintenance", 0, "", [], self.handle_maintenance, self.maintenance_help_str),
             ("update", 0, "", [], self.handle_update, self.update_help_str),
             ("enable", 1, "f", ["force"], self.handle_enable, self.enable_help_str),
             ("disable", 1, "f", ["force"], self.handle_disable, self.disable_help_str),
             ("start", None, "f", ["force"], self.handle_start, self.start_help_str),
             ("stop", None, "f", ["force"], self.handle_stop, self.stop_help_str),
             ("set-host", 1, "", [], self.handle_set_host, self.set_host_help_str),
             ("set-root-pwd", 1, "", [], self.handle_set_root_pwd, self.set_root_pwd_help_str),
             ("set-admin-pwd", 1, "", [], self.handle_set_admin_pwd, self.set_admin_pwd_help_str),
             ("write-service-cfg", 0, "", [], self.handle_write_service_cfg, self.write_service_cfg_help_str),
             ("write-network-cfg", 0, "", [], self.handle_write_network_cfg, self.write_network_cfg_help_str),
             ("write-issue", 0, "", [], self.handle_write_issue, self.write_issue_help_str),
             ("restart-services", 0, "", [], self.handle_restart_services, self.restart_services_help_str),
             ("restart-network", 0, "", [], self.handle_restart_network, self.restart_network_help_str))

    # Print the program usage.
    def print_usage(self, stream):
        stream.write(self.global_help_str)

    # Enable logging to syslog.
    def enable_syslog(self):
        class SyslogStream:
            def write(self, msg):
                syslog.syslog(syslog.LOG_INFO, msg)
        
        syslog.openlog(os.path.basename(sys.argv[0]), 0, syslog.LOG_DAEMON)
        stream = SyslogStream()
        self.stdout = stream
        self.stderr = stream
    
    # Return the list of commands matching the name specified.
    def get_cmd_list_from_name(self, name):
        l = []
        for entry in self.cmd_dispatch_table:
            if entry[0].startswith(name): l.append(entry)
        return l

    # Setup readline.
    def setup_readline(self):
        cmd_name_list = []
        for entry in self.cmd_dispatch_table: cmd_name_list.append(entry[0])
        completer = readline_completer(cmd_name_list)
        readline.set_completer_delims("")
        readline.parse_and_bind("tab: complete")
        readline.set_completer(completer.complete)

    # Return the parsed output of nestat(1) describing the address/port pairs
    # being listened to.
    def get_netstat_output(self):
        s = ""
        s += "Address:port          pid/process\n"
        s += "---------------------------------\n"
        for line in get_cmd_output(["/bin/netstat", "-nltp"]).splitlines():
            fields = line.split()
            if len(fields) < 7 or not fields[0].startswith("tcp"): continue
            s += "%s%s\n" % (fields[3].ljust(22), fields[6])
        return s
    
    # Return the parsed output of ifconfig(1) describing the status of the
    # network interfaces
    def get_ifconfig_output(self):
        s = ""
        remaining = 0
        for line in get_cmd_output(["/sbin/ifconfig", "-a"]).splitlines():
            if line == "":
                s += "\n"
                remaining = 0
            elif not line[0].isspace():
                remaining = 2
                s += line + "\n"
            elif remaining:
                s += line + "\n"
                remaining -= 1
        return s.strip() + "\n"
    
    # Return a string containing the server service state.
    def get_server_service_summary_string(self):
        s = ""
        for service in self.service_manager.service_list:
            s += service.name + ": "
            status = service.get_status()
            if status.is_present: s += "present"
            else: s += "absent"
            s += ", "
            if status.is_enabled: s += "enabled"
            else: s += "disabled"
            s += ", "
            if status.run_status == 0: s += "stopped"
            elif status.run_status == 1: s += "halfway stopped"
            else: s += "running"
            s += "\n"
        return s
    
    # Return a string describing the user service state.
    def get_user_service_summary_string(self):
        s = ""
        for key in self.config.user_service_name_dict:
            value = self.config.user_service_name_dict[key]
            s += value + ": "
            if self.config[key + "_service"]: s += "enabled"
            else: s += "disabled"
            s += "\n"
        return s
    
    # Return a formatted string for the product name and version.
    def get_formatted_product_name_and_version(self):
        version_tuple = self.config.get_product_version_tuple()
        return "Teambox Platform %i.%i" % (version_tuple[0], version_tuple[1])
     
    # Return a formatted string for the server mode.
    def get_formatted_server_mode(self):
        if self.config.production_mode: return "\033[44mProduction Mode\033[0m"
        return "\033[43mMaintenance Mode\033[0m"
     
    # Return a formatted string for the error banner.
    def get_formatted_error_banner(self):
        if self.config.get_health_issue_string(self.service_manager):
            return "\033[41m**Server must be reconfigured**\033[0m"
        return ""
    
    # Return a formatted string for the web configuration interface URL.
    def get_formatted_web_config_url(self):
        if not len(self.config.admin_pwd) or self.service_manager.get_service("apache").run_status() != 2:
            return ""
        return "Web configuration URL: \033[35mhttps://" + get_current_server_address() + ":9001\033[0m"
    
    # Return a formatted string for the configuration information.
    def get_formatted_config_info(self, status_flag=1, bar_flag=1):
        product = self.get_formatted_product_name_and_version()
        mode = self.get_formatted_server_mode()
        health = self.config.get_health_issue_string(self.service_manager)
        url = self.get_formatted_web_config_url()
        user_summary = self.get_user_service_summary_string()
        eth0 = self.config.eth0
        cur_addr = get_current_server_address()
        s = ""
        
        if bar_flag:
            s += "================================= Configuration ================================\n"
            s += "\n"
        
        s += "IP address: "
        if len(cur_addr): s += cur_addr
        else: s += "none"
        s += " "
        
        if eth0.method == "static":
            s += "(static)\n"
            s += "   Netmask: %s\n" % (eth0.netmask)
            s += "   Gateway: %s\n" % (eth0.gateway)
            s += "   Nameservers: %s\n" % (" ".join(self.config.dns_addr_list))
            if eth0.ip != cur_addr: s += "  \033[41mWarning: configured IP is %s\033[0m\n" % (eth0.ip)
        else:
            s += "(dhcp)\n"
        
        s += "Fully qualified domain name: " + self.config.get_fqdn() + "\n"
        s += "\n"
        
        s += "Root account password: "
        if self.config.is_root_pwd_locked(): s += "not set"
        else: s += "set"
        s += "\n"
        
        s += "Administration password: "
        if len(self.config.admin_pwd): s += "set"
        else: s += "not set"
        s += "\n"
        
        s += "\n"
        
        if len(url): s += url + "\n\n"
    
        if status_flag:
            if bar_flag:
                s += "=================================== Status ===================================\n"
                s += "\n"
            s += product + "  " + mode + "\n"
            if health: s += "\033[41mError: " + health + "\033[0m\n"
            else: s += "\033[1;32mThe services are running normally.\033[0m\n"
            s += "\n"
            s += user_summary + "\n"
        
        if bar_flag:
            s += "================================================================================\n"
        
        return s
    
    # This method prompts the user for one or several IP addresses. If the
    # address supplied is incorrect, a ValueError exception is raised.
    def prompt_for_ip(self, prompt, multi_flag=0):
        while 1:
            try:
                res = prompt_string(prompt)
                if multi_flag:
                    addr_list = res.split()
                    if not len(addr_list): raise ValueError
                    for addr in addr_list: parse_dotted_ip(addr)
                    return addr_list
                else:
                    parse_dotted_ip(res)
                    return res
            except ValueError:
                print "The address you have specified is invalid.\n"
                if not get_confirm("Try again?"): raise ValueError
    
    # Helper method for _configure_dhcp() and _configure_static_ip().
    def _configure_iface_helper(self):
        try:
            self.config.save_master_config()
            self.config.write_network_config()
            self.service_manager.restart_network()
            print("Reconfiguration successful. Current address: " + get_current_server_address())
        except Exception, e:
            self.stderr.write("Error: " + str(e) + ".\n")
            return
    
    # This method configures the machine to use DHCP.
    def _configure_dhcp(self):
        eth0 = self.config.eth0
        eth0.method = "dhcp"
        self._configure_iface_helper()

    # This method configures the machine to use a static IP.
    def _configure_static_ip(self):
        try:
            eth0 = self.config.eth0
            eth0.method = "static"
            eth0.ip = self.prompt_for_ip("Static IP address:")
            eth0.netmask = self.prompt_for_ip("Static IP netmask:")
            eth0.gateway = self.prompt_for_ip("Gateway IP address:")
            self.config.dns_addr_list = self.prompt_for_ip("Nameserver IP list:", 1)
        except ValueError: return
        self._configure_iface_helper()
    
    # This method changes the FQDN of the machine.
    def _configure_fqdn(self):
        print("")
        try:
            host = prompt_string("Host:")
            self.config.set_host(self.service_manager, host, self.stdout)
        except Exception, e:
            self.stderr.write("Error: " + str(e) + ".\n")
            return
    
    # Handle the change password loop. Return the password if provided, or "" if
    # the user aborted the operation.
    def _configure_pwd_helper(self):
        print("")
        while 1:
            pwd1 = getpass.getpass("Enter password: ")
            
            if pwd1 == "":
                print "You did not provide a password.\n"
                if not get_confirm("Try again?"): return ""
                continue
            
            pwd2 = getpass.getpass("Confirm password: ")
            
            if pwd1 != pwd2:
                print "Sorry, the passwords do not match.\n"
                if not get_confirm("Try again?"): return ""
                continue
        
            return pwd1
    
    # Change the root password.
    def _configure_root_pwd(self):
        pwd = self._configure_pwd_helper()
        if pwd:
            self.config.set_root_pwd(pwd)
            print "The root account password has been changed."

    # Change the administration password.
    def _configure_admin_pwd(self):
        pwd = self._configure_pwd_helper()
        if pwd:
            self.config.set_admin_pwd(pwd)
            print "The administration password has been changed."
    
    # Command handlers.
    def handle_help(self, opts, args):
        
        # Print help about the command specified, if there is one.
        if len(args):
            l = self.get_cmd_list_from_name(args[0])
            if len(l) == 0:
                self.stdout.write("No such command.\n")
                self.print_usage(self.stdout)
            else:
                first = 1
                for cmd in l:
                    if not first: self.stdout.write("\n")
                    self.stdout.write(cmd[5])
                    first = 0
        
        # Print global help.
        else:
            self.print_usage(self.stdout)

    def handle_info(self, opts, args):
        self.stdout.write(self.get_formatted_config_info())
    
    def handle_health(self, opts, args):
        s = self.config.get_health_issue_string(self.service_manager)
        if s == "": s = "OK"
        s += "\n"
        self.stdout.write(s)
    
    def handle_ifconfig(self, opts, args):
        self.stdout.write(self.get_ifconfig_output())

    def handle_netstat(self, opts, args):
        self.stdout.write(self.get_netstat_output())
        
    def handle_services(self, opts, args):
        s = ""
        s += "=== User services ===\n"
        s += self.get_user_service_summary_string()
        s += "\n"
        s += "=== Server services ===\n"
        s += self.get_server_service_summary_string()
        self.stdout.write(s)
     
    def handle_setup(self, opts, args):
        
        # Show the configuration to the user.
        self.stdout.write(self.get_formatted_config_info(0, 1))
         
        # Prompt the user for an action.
        while 1:
            print "\nChoose an action:"
            print "  a) Reconfigure the machine to use DHCP."
            print "  b) Reconfigure the machine to use a static IP."
            print "  c) Change the fully qualified domain name."
            print "  d) Change the root account password. This allows SSH access."
            print "  e) Change the administration password."
            print "  f) Show the current configuration."
            print "  *) Exit."
            
            choice = prompt_string("\nChoice:")
            
            if choice == "a": self._configure_dhcp()
            elif choice == "b": self._configure_static_ip()
            elif choice == "c": self._configure_fqdn()
            elif choice == "d": self._configure_root_pwd()
            elif choice == "e": self._configure_admin_pwd()
            elif choice == "f": self.stdout.write(self.get_formatted_config_info(0, 1))
            else: break
            
        # Show the info about the web interface if required.
        url = self.get_formatted_web_config_url()
        if len(url): self.stdout.write("\n" + url + "\n\n")
    
    def handle_production(self, opts, args):
        self.config.switch_to_production_mode(self.service_manager, 1, self.stdout)

    def handle_maintenance(self, opts, args):
        self.config.switch_to_maintenance_mode(self.service_manager, 1, self.stdout)

    def handle_update(self, opts, args):
        pass
    
    def _handle_enable_disable_helper(self, opts, args, enabled_flag):
        
        # Get the service name.
        name = args[0]
        user_service_name = name + "_service"
        
        # Get the force flag.
        force_flag = 0
        for k, v in opts:
            if k == "-f" or k == "--force": force_flag = 1
        
        # This is a Teambox service.
        if self.service_manager.service_dict.has_key(name):
            service = self.service_manager.get_service(name)
            if force_flag or bool(service.is_enabled()) != bool(enabled_flag):
                service.set_enabled(enabled_flag)
        
        # This is a user-visible service.
        elif self.config.prop_set.has_key(user_service_name):
            self.config[user_service_name] = int(enabled_flag)
            self.config.save_master_config()
        
        # No such service, throw exception.
        else: self.service_manager.get_service(name)
        
    def handle_enable(self, opts, args):
        self._handle_enable_disable_helper(opts, args, 1)
        
    def handle_disable(self, opts, args):
        self._handle_enable_disable_helper(opts, args, 0)

    def _handle_start_stop_helper(self, opts, args, start_flag):
        
        # Get the force flag.
        force_flag=0
        for k, v in opts:
            if k == "-f" or k == "--force": force_flag = 1
        
        # Get the service list.
        service_list = []
        for arg in args: service_list.append(arg)
        if not len(args): service_list = None
        
        # Call the method.
        if start_flag: method = self.service_manager.start_service
        else: method = self.service_manager.stop_service
        method(service_list, force_flag, self.stdout)
        
    def handle_start(self, opts, args):
        self._handle_start_stop_helper(opts, args, 1)
        
    def handle_stop(self, opts, args):
        self._handle_start_stop_helper(opts, args, 0)

    def handle_set_host(self, opts, args):
        self.config.set_host(self.service_manager, args[0], self.stdout)

    def handle_set_root_pwd(self, opts, args):
        self.config.set_root_pwd(args[0])

    def handle_set_admin_pwd(self, opts, args):
        self.config.set_admin_pwd(args[0])
        
    def handle_write_service_cfg(self, opts, args):
        self.config.normalize_service_config()
        self.config.write_service_config()

    def handle_write_network_cfg(self, opts, args):
        self.config.write_network_config()
        
    def handle_write_issue(self, opts, args):
        def act(action_text): return "\033[1;36m" + action_text + "\033[0m"
        
        product = self.get_formatted_product_name_and_version()
        mode = self.get_formatted_server_mode()
        banner = self.get_formatted_error_banner()
        url = self.get_formatted_web_config_url()
        
        s = ""
        s += "\033\133\110\033\133\062\112"
        s += product + "  " + mode
        if banner: s += "  " + banner
        s += "\n"
        s += " Type " + act("setup") + " to setup the machine.\n"
        s += " Type " + act("login") + " to login as root on the machine.\n"
        s += " Type " + act("info") + " to display the basic configuration.\n"
        s += " Type " + act("maintenance") + " or " + act("production") + " to switch the server mode.\n"
        s += " Type " + act("update") + " to update the software.\n"
        if url: s += "\n" + url + "\n"
        s += s
        
        write_file("/etc/issue", s)
        
    def handle_restart_services(self, opts, args):
        self.config.normalize_service_config()
        self.config.write_service_config()
        self.service_manager.restart_services(output_stream=self.stdout)
    
    def handle_restart_network(self, opts, args):
        self.config.write_network_config()
        self.service_manager.restart_network()

    # Run the specified command. This method must be passed a list containing
    # the command name and its arguments. The method returns 0 on success, 1 on
    # failure.
    def run_command(self, input_arg_list):
    
        if self.echo_cmd_flag:
            s = "Running command: " 
            for arg in input_arg_list: s += arg + " "
            s += "\n"
            self.stdout.write(s)
        
        cmd_list = self.get_cmd_list_from_name(input_arg_list[0])
        if len(cmd_list) != 1:
            if len(cmd_list) == 0:
                self.stderr.write("No such command.\n")
            else: 
                self.stderr.write("Ambiguous command: ")
                for cmd in cmd_list: self.stderr.write(cmd[0] + " ")
                self.stderr.write("\n")
            return 1
            
        cmd = cmd_list[0]
        
        # Parse the options of the command.
        try: cmd_opts, cmd_args = getopt.getopt(input_arg_list[1:], cmd[2], cmd[3])
        except getopt.GetoptError, e:
            self.stderr.write("Command options error: %s.\n\n" % (str(e)))
            self.stderr.write(cmd[5])
            return 1
       
        # Verify the number of arguments.
        if cmd[1] != None and cmd[1] != len(cmd_args):
            self.stderr.write("Invalid number of arguments.\n\n")
            self.stderr.write(cmd[5])
            return 1
        
        # Load the root configuration node.
        if cmd[0] != "help": self.config.load_master_config()
    
        # Call the handler.
        cmd[4](cmd_opts, cmd_args)

    # This method implements a high-level exception handler.
    def high_level_exception_handler(self, e, ignore_error=0):
        
        # Raise system exit exceptions.
        if isinstance(e, SystemExit): raise e
        
        # Ignore interruptions.
        elif isinstance(e, KeyboardInterrupt) or isinstance(e, EOFError): return
         
        # Print errors, exit if requested.
        else:
            self.stderr.write("Error: " + str(e) + ".\n")
            if ignore_error: return
            sys.exit(1)

    # Loop processing commands.
    def handle_shell_mode(self):
        
        # Setup readline.
        self.setup_readline()
        
        # Print greeting.
        s = "Teambox platform shell.\n" +\
            "Type 'help' for help.\n" +\
            "\n"
        self.stdout.write(s)
        
        while 1:
            # Wait for command.
            cmd_line = string.split(raw_input("> "))
            if len(cmd_line) == 0: continue
            
            # Run the command.
            try: self.run_command(cmd_line)
            
            # Ignore interrupts.
            except self.trapped_exception_list, e: self.high_level_exception_handler(e, 1)
            
            # Add an empty line so that it looks pretty.
            finally: self.stdout.write("\n")

def main():
    help_flag = 0
    syslog_flag = 0
        
    # Set the umask.
    os.umask(0022)
    
    # Create an instance of the shell.
    shell = PlatShell()
    
    # Parse the global options.
    try: opts, args = getopt.getopt(sys.argv[1:], "hse", ["help", "syslog", "echo"])
    except getopt.GetoptError, e:
	sys.stderr.write("Options error: %s.\n\n" % (str(e)))
	shell.print_usage(sys.stderr)
	sys.exit(1)
    
    for k, v in opts:
	if k == "-h" or k == "--help": help_flag = 1
	elif k == "-s" or k == "--syslog": syslog_flag = 1
	elif k == "-e" or k == "--echo": shell.echo_cmd_flag = 1
    
    # Handle help.
    if help_flag:
        shell.handle_help({}, args)
        sys.exit(0)
    
    # Setup syslog.
    if syslog_flag: shell.enable_syslog()
    
    # Get the invokation name.
    invoked_name = os.path.basename(sys.argv[0])
    
    wait_for_return = 0
    
    # Dispatch.
    try:
        # Handle special login modes.
        if invoked_name != "klogin_debug" and invoked_name.startswith("klogin_"):
            wait_for_return = 1
            cmd = invoked_name[7:]
            sys.exit(shell.run_command([cmd]))
        
        # Handle issue.
        elif invoked_name == "issue.script":
            sys.exit(shell.run_command(["write-issue"]))
        
        # Handle shell_mode.
        elif not len(args):
            shell.handle_shell_mode()
        
        # Run the specified command.
        else:
            sys.exit(shell.run_command(args))
    
    # Handle the exceptions.
    except shell.trapped_exception_list, e: shell.high_level_exception_handler(e, 0)
    
    # Wait before exiting if necessary.
    finally:
        if wait_for_return:
            sys.stdout.write("\n\n")
            sys.stdout.write(" Press 'Return' to return to the login prompt...\n")
            try: raw_input()
            except: pass
            sys.stdout.write("\n\n")


# Allow import of this module.
if __name__ == "__main__": main()

