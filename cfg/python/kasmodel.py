import time, pwd
from kasmodeltool import *
from ksort import *
from kfile import *
from krun import *
from kifconfig import *

# This class represents a service running on a Teambox server.
class ServerService:
    
    # 'name' is the programmatic name of the service. 'dep_name_list' contains
    # the name of the services on which this service depends, in order.
    def __init__(self, name, dep_name_list):
        
        # Name of the service.
        self.name = name
        
        # List containing the name of the services on which this service
        # depends, in order.
        self.dep_name_list = dep_name_list
        
        # Reference to the config manager.
        self.manager = None
        
        # Position of this service in the global order of the services.
        self.pos = -1
    
    # Return the path to the init script symlink specified in /etc/rc2.d/.
    def _get_init_symlink_path(self, name, level):
        return "/etc/rc2.d/S%i%s" % (level, name)
     
    # This method returns true if the service is enabled according to the init
    # script symlink specified in /etc/rc2.d/.
    def is_enabled_according_to_init_script(self, name, level):
        path = self._get_init_symlink_path(name, level)
        return os.path.isfile(path) or os.path.islink(path)
    
    # This method enables the service with the init script symlink in
    # /etc/rc2.d/.
    def enable_with_init_script(self, name, level, enabled_flag):
        path = self._get_init_symlink_path(name, level)
        if enabled_flag: 
            if not os.path.isfile(path): os.symlink("/etc/init.d/" + name, path)
        else:
            delete_file(path)
     
    # This method returns true if the service is running according to the PID
    # file specified.
    def is_running_according_to_pid_file(self, pid_file):
        try:
            pid = read_file(pid_file).strip()
            if pid.isdigit() and os.path.isdir("/proc/" + pid): return 1
        except: return 0
    
    # This method returns the status of the KCD service using the lock file
    # specified.
    def get_kcd_status_from_lock_file(self, lock_file):
        try:
            status = get_cmd_output("/usr/bin/kcd query -P " + lock_file).strip()
            if status == "stopped": return 0
            elif status == "running": return 2
            else: return 1
        except: return 0
    
    # Return an object having three properties: is_present, is_enabled,
    # run_status.
    #
    # Run status codes:
    # - 0: the service is fully stopped.
    # - 1: the service is halfway stopped.
    # - 2: the service is fully running.
    def get_status(self):
        store = PropStore()
        store.is_present = self.is_present()
        store.is_enabled = self.is_enabled()
        store.run_status = self.run_status()
        return store
    
    # This virtual method is called to determine whether the service is
    # installed on the machine.
    def is_present(self):
        return 0
    
    # This virtual method is called to determine whether the service is enabled.
    def is_enabled(self):
        return 0
    
    # This virtual method is called to determine whether the service is running.
    # Run status codes:
    # - 0: the service is fully stopped.
    # - 1: the service is halfway stopped.
    # - 2: the service is fully running.
    def run_status(self):
        return 0
    
    # This virtual method is called to enable or disable the service.
    def set_enabled(self, enabled_flag):
        pass
    
    # This virtual method is called to start the service. An exception should be
    # thrown if the service cannot be started. This method does nothing if the
    # service is started indirectly by another service, such as Apache.
    def start_service(self):
        pass

    # This virtual method is called to stop the service. An exception should be
    # thrown if the service cannot be stopped.
    def stop_service(self):
        pass

# Postgres service. 
class PostgresService(ServerService):
    
    def __init__(self):
        ServerService.__init__(self, "postgres", [])
        self.pid_file = "/var/run/postgresql/8.4-teambox.pid"
    
    def is_present(self):
        return os.path.isdir("/usr/lib/postgresql/8.4")
    
    def is_enabled(self):
        return self.is_enabled_according_to_init_script("postgresql-8.4", 19)
    
    def run_status(self):
        # Note: the PID file is not world readable. This method fails if the
        # process is not running as root.
        if self.is_running_according_to_pid_file(self.pid_file): return 2
        return 0
        
    def set_enabled(self, enabled_flag):
        self.enable_with_init_script("postgresql-8.4", 19, enabled_flag)
    
    def start_service(self):
        get_cmd_output("/etc/init.d/postgresql-8.4 start")
    
    def stop_service(self):
        get_cmd_output("/etc/init.d/postgresql-8.4 stop")
        # Note: buggy stop script won't delete PID file properly sometimes.
        delete_file(self.pid_file)
    
# Apache service. 
class ApacheService(ServerService):
    def __init__(self):
        ServerService.__init__(self, "apache", ["postgres"])
     
    def is_present(self):
        return os.path.isfile("/usr/sbin/apache2")
    
    def is_enabled(self):
        return self.is_enabled_according_to_init_script("apache2", 91)
        
    def run_status(self):
        if self.is_running_according_to_pid_file("/var/run/apache2.pid"): return 2
        return 0
    
    def set_enabled(self, enabled_flag):
        self.enable_with_init_script("apache2", 91, enabled_flag)
    
    def start_service(self):
        get_cmd_output("/etc/init.d/apache2 start")
    
    def stop_service(self):
        get_cmd_output("/etc/init.d/apache2 stop")
    
    # Reload Apache configuration.
    def reload_config(self):
        get_cmd_output("/etc/init.d/apache2 reload")

# This class represents a service provided by Teambox.
class TeamboxService(ServerService):
    def __init__(self, name, depend_list):
        ServerService.__init__(self, name, depend_list)
    
    # Enable or disable the service in Apache.
    def set_enabled_in_apache(self, enabled_flag):
        if enabled_flag: get_cmd_output("a2ensite " + self.name)
        else: get_cmd_output("a2dissite " + self.name)
    
    # Return true if the service is present in Apache.
    def is_present_in_apache(self):
        return os.path.isfile("/etc/apache2/sites-available/" + self.name)
    
    # Return true if the service is enabled in Apache.
    def is_enabled_in_apache(self):
        return self.is_present_in_apache() and os.path.isfile("/etc/apache2/sites-enabled/" + self.name)
    
# Tbxsosd service.
class TbxsosdService(TeamboxService):
    def __init__(self):
        TeamboxService.__init__(self, "tbxsosd", ["postgres"])
    
    def is_present(self):
        return os.path.isfile("/usr/bin/tbxsosd")
    
    def is_enabled(self):
        return self.is_enabled_according_to_init_script("tbxsosd", 40)
    
    def run_status(self):
        if self.is_running_according_to_pid_file("/var/run/tbxsosd.pid"): return 2
        return 0
    
    def set_enabled(self, enabled_flag):
        self.enable_with_init_script("tbxsosd", 40, enabled_flag)
    
    def start_service(self):
        get_cmd_output("/etc/init.d/tbxsosd start")

    def stop_service(self):
        get_cmd_output("/etc/init.d/tbxsosd stop")

# KCD service in frontend mode.
class KcdService(TeamboxService):
    def __init__(self):
        TeamboxService.__init__(self, "kcd", ["postgres"])
    
    def is_present(self):
        return os.path.isfile("/usr/bin/kcd")
    
    def is_enabled(self):
        return self.is_enabled_according_to_init_script("kcd", 40)

    def run_status(self):
        return self.get_kcd_status_from_lock_file("/var/lock/kcd.lock")
    
    def set_enabled(self, enabled_flag):
        self.enable_with_init_script("kcd", 40, enabled_flag)
    
    def start_service(self):
        get_cmd_output("/etc/init.d/kcd start")

    def stop_service(self):
        get_cmd_output("/etc/init.d/kcd stop")

# KCD service in notification mode.
class KcdNotifService(TeamboxService):
    def __init__(self):
        TeamboxService.__init__(self, "kcdnotif", ["postgres"])
    
    def is_present(self):
        return os.path.isfile("/usr/bin/kcd")
    
    def is_enabled(self):
        return self.is_enabled_according_to_init_script("kcdnotif", 40)

    def run_status(self):
        return self.get_kcd_status_from_lock_file("/var/lock/kcdnotif.lock")
    
    def set_enabled(self, enabled_flag):
        self.enable_with_init_script("kcdnotif", 40, enabled_flag)
    
    def start_service(self):
        get_cmd_output("/etc/init.d/kcdnotif start")

    def stop_service(self):
        get_cmd_output("/etc/init.d/kcdnotif stop")
    
# Kasmond service.
class KasmondService(TeamboxService):
    def __init__(self):
        TeamboxService.__init__(self, "kasmond", ["kcd"])
    
    def is_present(self):
        return os.path.isfile("/usr/bin/kasmond")
    
    def is_enabled(self):
        return self.is_enabled_according_to_init_script("kasmond", 40)
        
    def run_status(self):
        if self.is_running_according_to_pid_file("/var/run/kasmond.pid"): return 2
        return 0
        
    def set_enabled(self, enabled_flag):
        self.enable_with_init_script("kasmond", 40, enabled_flag)
    
    def start_service(self):
        get_cmd_output("/etc/init.d/kasmond start")
   
    def stop_service(self):
        get_cmd_output("/etc/init.d/kasmond stop")
        get_cmd_output("/usr/bin/kasmond --unmount")

# Kwsfetcher service.
class KwsfetcherService(TeamboxService):
    def __init__(self):
        TeamboxService.__init__(self, "kwsfetcher", ["postgres"])
    
    def is_present(self):
        return os.path.isfile("/usr/bin/kwsfetcher")
    
    def is_enabled(self):
        return self.is_enabled_according_to_init_script("kwsfetcher", 40)
    
    def run_status(self):
        if self.is_running_according_to_pid_file("/var/run/kwsfetcher.pid"): return 2
        return 0
    
    def set_enabled(self, enabled_flag):
        self.enable_with_init_script("kwsfetcher", 40, enabled_flag)
    
    def start_service(self):
        get_cmd_output("/etc/init.d/kwsfetcher start")
   
    def stop_service(self):
        get_cmd_output("/etc/init.d/kwsfetcher stop")

# Tbxsos-configd service.
class TbxsosConfigdService(TeamboxService):
    def __init__(self):
        TeamboxService.__init__(self, "tbxsos-configd", ["postgres", "apache"])
    
    def is_present(self):
        return os.path.isfile("/usr/bin/tbxsos-configd")
    
    def is_enabled(self):
        return self.is_enabled_according_to_init_script("tbxsos-configd", 40)
    
    def run_status(self):
        if self.is_running_according_to_pid_file("/var/run/tbxsos-configd.pid"): return 2
        return 0
    
    def set_enabled(self, enabled_flag):
        self.enable_with_init_script("tbxsos-configd", 40, enabled_flag)
    
    def start_service(self):
        get_cmd_output("/etc/init.d/tbxsos-configd start")
   
    def stop_service(self):
        get_cmd_output("/etc/init.d/tbxsos-configd stop")
    
# Tbxsos-config service.
class TbxsosConfigService(TeamboxService):
    def __init__(self):
        TeamboxService.__init__(self, "tbxsos-config", ["postgres", "apache"])
    
    def is_present(self):
        return self.is_present_in_apache()
        
    def is_enabled(self):
        return self.is_enabled_in_apache()
    
    def run_status(self):
        if self.is_enabled() and self.manager.get_service("apache").run_status() == 2: return 2
        return 0
    
    def set_enabled(self, enabled_flag):
        self.set_enabled_in_apache(enabled_flag)
    
# Kas_cfg service.
class KasCfgService(TeamboxService):
    def __init__(self):
        TeamboxService.__init__(self, "kas_cfg", ["postgres", "apache"])
    
    def is_present(self):
        return self.is_present_in_apache()
        
    def is_enabled(self):
        return self.is_enabled_in_apache()
    
    def run_status(self):
        if self.is_enabled() and self.manager.get_service("apache").run_status() == 2: return 2
        return 0
    
    def set_enabled(self, enabled_flag):
        self.set_enabled_in_apache(enabled_flag)

# Web bridge service.
class WebBridgeService(TeamboxService):
    def __init__(self):
        TeamboxService.__init__(self, "web_bridge", ["postgres", "apache"])
    
    def is_present(self):
        return self.is_present_in_apache()
        
    def is_enabled(self):
        return self.is_enabled_in_apache()
    
    def run_status(self):
        if self.is_enabled() and self.manager.get_service("apache").run_status() == 2: return 2
        return 0
    
    def set_enabled(self, enabled_flag):
        self.set_enabled_in_apache(enabled_flag)

# KWMO service.
class KwmoService(TeamboxService):
    def __init__(self):
        TeamboxService.__init__(self, "kwmo", ["web_bridge"])
   
    def is_present(self):
        return self.is_present_in_apache()
        
    def is_enabled(self):
        return self.is_enabled_in_apache()
    
    def run_status(self):
        if self.is_enabled() and self.manager.get_service("apache").run_status() == 2: return 2
        return 0
    
    def set_enabled(self, enabled_flag):
        self.set_enabled_in_apache(enabled_flag)

# Freemium web service.
class FreemiumWebService(TeamboxService):
    def __init__(self):
        TeamboxService.__init__(self, "freemium_web", ["web_bridge"])
   
    def is_present(self):
        return self.is_present_in_apache()
        
    def is_enabled(self):
        return self.is_enabled_in_apache()
    
    def run_status(self):
        if self.is_enabled() and self.manager.get_service("apache").run_status() == 2: return 2
        return 0
    
    def set_enabled(self, enabled_flag):
        self.set_enabled_in_apache(enabled_flag)

# This class manages the server services, including the network.
class ServiceManager:
    def __init__(self):
        
        # Dictionary containing the services.
        self.service_dict = {}
        
        # List containing the services, sorted by dependency.
        self.service_list = None
        
        # Reversed service list.
        self.reverse_service_list = None
        
        # Add the services.
        self._add_service(PostgresService())
        self._add_service(ApacheService())
        self._add_service(TbxsosdService())
        self._add_service(KcdService())
        self._add_service(KcdNotifService())
        self._add_service(KasmondService())
        self._add_service(KwsfetcherService())
        self._add_service(TbxsosConfigService())
        self._add_service(TbxsosConfigdService())
        self._add_service(KasCfgService())
        self._add_service(WebBridgeService())
        self._add_service(KwmoService())
        self._add_service(FreemiumWebService())
        
        # Essential service list.
        self.essential_service_list = [ self.get_service("postgres"), self.get_service("apache") ]
        
        # Resolve the dependencies.
        self._resolve_dependencies()
        
    # Return a function that compare services by position.
    def _get_pos_cmp_func(self):
        def pos_cmp(a, b): return int.__cmp__(a.pos, b.pos)
        return pos_cmp
    
    # Add a service to the manager.
    def _add_service(self, service):
        self.service_dict[service.name] = service
        service.manager = self
    
    # Resolve the dependencies.
    def _resolve_dependencies(self):
    
        # Sort by name to get a deterministic behavior.
        name_list = self.service_dict.keys()
        name_list.sort()
        self.service_list = []
        for name in name_list: self.service_list.append(self.get_service(name))
        
        # Topological sort.
        partial_order_list = []
        for service in self.service_list:
            for dep_name in service.dep_name_list:
                partial_order_list.append([self.get_service(dep_name), service])
        self.service_list = topological_sort(self.service_list, partial_order_list)
        if self.service_list == None: raise Exception("dependency loop")
        self.reverse_service_list = self.service_list[:]
        self.reverse_service_list.reverse()
        
        # Assign positions.
        for i in range(0, len(self.service_list)): self.service_list[i].pos = i
     
    # Return the service having the name specified. An exception is raised if
    # there is no such service.
    def get_service(self, name):
        if not self.service_dict.has_key(name): raise Exception("service '%s' does not exist" % (name))
        return self.service_dict[name]
    
    # Start the services specified in 'start_list'. If 'start_list' is 'None',
    # all the services that are present and enabled are started. If 'force_flag'
    # is true, the services are started even if they seem to be running. If
    # 'output_stream' is not 'None', some output describing what is happening is
    # written to that stream. All services are started in dependency order.
    def start_service(self, start_list = None, force_flag=0, output_stream=None):
        if start_list == None:
            serv_list = []
            for service in self.service_list:
                if service.is_present() and service.is_enabled(): serv_list.append(service)
        else:
            serv_list = [ self.get_service(name) for name in start_list ]
        
        serv_list.sort(self._get_pos_cmp_func())
        
        for service in serv_list:
            if not force_flag and service.run_status() == 2:
                if output_stream: output_stream.write("%s: already running, skipping...\n" % (service.name))
                continue
            if output_stream: output_stream.write("%s: starting...\n" % (service.name))
            service.start_service()
    
    # Stop the services specified in 'stop_list'. If 'stop_list' is 'None', all
    # the services that are present are stopped. If 'force_flag' is true, the
    # services are stopped even if they seem to be stopped. If 'output_stream'
    # is not 'None', some output describing what is happening is written to that
    # stream. All services are stopped in reverse dependency order.
    def stop_service(self, stop_list = None, force_flag=0, output_stream=None):
        serv_list = []
        if stop_list == None:
            for service in self.service_list:
                if service.is_present(): serv_list.append(service)
        else:
            for name in stop_list:
                service = self.get_service(name)
                if service.is_present(): serv_list.append(service)
        
        serv_list.sort(self._get_pos_cmp_func())
        serv_list.reverse()
        
        for service in serv_list:
            if not force_flag and service.run_status() == 0:
                if output_stream: output_stream.write("%s: already stopped, skipping...\n" % (service.name))
                continue
            if output_stream: output_stream.write("%s: stopping...\n" % (service.name))
            service.stop_service()
    
    # Stop all non-essential or disabled services then start all enabled
    # services.
    def restart_services(self, force_flag=0, output_stream=None):
        stop_list = []
        for service in self.service_list:
            if not service in self.essential_service_list or not service.is_enabled():
                stop_list.append(service.name)
        
        start_list = []
        for service in self.service_list:
            if service.is_enabled(): start_list.append(service.name)
        
        if output_stream: output_stream.write("* Stopping non-essential or disabled services:\n")
        self.stop_service(stop_list, force_flag, output_stream)
        
        if output_stream: output_stream.write("\n* Starting enabled services:\n")
        self.start_service(start_list, force_flag, output_stream)
    
    # Update the hostname.
    def reload_hostname(self):
        get_cmd_output(["hostname", "--file", "/etc/hostname"])
    
    # Reload the firewall rules.
    def reload_firewall_rules(self):
        get_cmd_output(["/etc/init.d/iptables.sh", "restart"])
    
    # Reload the network interfaces.
    def reload_network_iface(self):
        try:
            # Work around broken Debian scripts...
            get_cmd_output(["/sbin/ifdown", "--force", "eth0"])
            
            # The 'ifup' script sucks, we have to try to detect errors manually.
            proc = Popen(args = ["/sbin/ifup", "--force", "eth0"], stdout = PIPE, stderr = PIPE, shell = False)
            (out_text, err_text) = proc.communicate()
            if proc.returncode != 0: raise Exception(err_text.strip().rstrip('.'))
            res_text = out_text + err_text
            if res_text.find("Failed") != -1: raise Exception(res_text)
            
            # Try to restart networking by the official way.
            get_cmd_output(["/etc/init.d/networking", "restart"])
        
        except Exception, e:
            raise Exception("failed to configure network interfaces: " + str(e))
    
    # Call reload_hostname(), reload_firewall_rules() and reload_network_iface().
    def restart_network(self):
        self.reload_hostname()
        self.reload_firewall_rules()
        self.reload_network_iface()
    
# This class represents a network interface.
class NetworkInterfaceConfig(AbstractConfigNode):
    prop_set = ConfigPropSet()
    prop_set.add_prop('name', "eth0", "Name of the interface, e.g. 'eth0'.")
    prop_set.add_prop('method', "dhcp", "Method used to assign an IP address to the interface: 'dhcp' or\n'static'.")
    prop_set.add_prop('ip', "", "Static IP address associated to the interface, if any.")
    prop_set.add_prop('netmask', "", "Netmask associated to the IP address, if any.")
    prop_set.add_prop('gateway', "", "Gateway associated to the interface, if any.")

# Represent the root configuration node.
class RootConfigNode(AbstractConfigNode):
    prop_set = ConfigPropSet()
    
    # Local host information.
    prop_set.add_prop('admin_pwd', '', "Local host administration password.")
    prop_set.add_prop('eth0', NetworkInterfaceConfig, "eth0 network interface")
    prop_set.add_prop('dns_addr_list',
                      Prop(model = PropModel(cls=ConfigList, cls_args=[str]),
                           doc = "DNS server addresses. Leave empty if using DHCP."))
    prop_set.add_prop("hostname", 'localhost', "Hostname of the machine. This does not include the domain.")
    prop_set.add_prop("domain", '', "Domain of the machine.")
    prop_set.add_prop('all_port_addr_list',
                      Prop(model = PropModel(cls=ConfigList, cls_args=[str, ['0.0.0.0/0']]),
                           doc = "List of IP addresses of the form X.X.X.X/X that have access " +
                                 "to all ports of this server."))
    prop_set.add_prop('config_port_addr_list',
                      Prop(model = PropModel(cls=ConfigList, cls_args=[str, ['0.0.0.0/0']]),
                           doc = "List of IP addresses of the form X.X.X.X/X that have access " +
                                 "to the configuration ports of this server."))
    prop_set.add_prop('sshd_line_list',
                      Prop(model = PropModel(cls=ConfigList, cls_args=[str]),
                           doc = "List of custom lines to insert into /etc/ssh/sshd_config."))
    prop_set.add_prop('tbxsos_service', 0, "True if the TBXSOS service has been enabled by the user.")
    prop_set.add_prop('freemium_service', 0, "True if the Freemium service has been enabled by the user.")
    prop_set.add_prop('mas_service', 0, "True if the MAS service has been enabled by the user.")
    prop_set.add_prop('wps_service', 0, "True if the WPS service has been enabled by the user.")
    
    
    # Remote hosts information.
    prop_set.add_prop('kps_host', '',
        "Host running the KPS. This hostname must be resolvable by everyone!")
    
    prop_set.add_prop('kcd_host', '',
        "Host running the KCD in KANP mode. This hostname must be resolvable by\n" + 
        "everyone!")

    prop_set.add_prop('kwmo_host', '',
        "Host running the KWMO interface. This hostname must be resolvable by\n" +
        "everyone!")
    
    prop_set.add_prop('kps_pwd', '', "Password to access the KPS. Default to admin password if left empty.")
    prop_set.add_prop('kcd_pwd', '', "Password to access the KCD. Default to admin password if left empty.")
    prop_set.add_prop('kwmo_pwd', '', "Password to access the KWMO. Default to admin password if left empty.")
    
    
    # Freemium-specific flags.
    prop_set.add_prop('freemium_autoregister', 0, "True if the users are allowed to auto-register")
    # Delayed until supported in KPS web interface.
    #prop_set.add_prop('freemium_org_id', 0L, "Organization ID used for the freemium service. 0 means auto-detect.")
    
    
    # KCD and kasmond-specific flags.
    
    prop_set.add_prop('kcd_enforce_restriction', 0, "True if usage restrictions are enforced.")
    prop_set.add_prop('kcd_listen_addr', "0.0.0.0", "Network address KCD listens to.")
    prop_set.add_prop('kcd_listen_port', 443, "Port KCD listens to.")

    prop_set.add_prop('kcd_kmod_binary_path', "/usr/bin/kmod", 
        "Path to the KMOD binary. This is used by KCD when it is running in KANP\n"
        + "mode.")

    prop_set.add_prop('kcd_kmod_db_path', "/etc/teambox/kcd/kmod_db", 
        "Path to the KMOD database. KMOD doesn't actually write in the DB, so it can be\n"
        + "shared among multiple KMOD instances.")

    prop_set.add_prop('kcd_vnc_cred_path', "/var/teambox/vnc_meta/vnc_cred",
        "Path to the VNC credential directory. This is used by KCD when it is running\n"
        + "in VNC meta proxy mode.")

    prop_set.add_prop('kcd_web_port', 80, 
        "Web server port. This is used by KCD when it is running in VNC meta proxy\n"
        + "mode.")

    prop_set.add_prop('kcd_web_link', 
        '"Click on the following link to access the workspace with your web\\nbrowser: %s\\n"',
        "Old-style web link included in messages inviting people to this KAS. This is\n"
        + "used by KCD when it is running in KANP mode.")

    prop_set.add_prop('kcd_invite_mail_kcd_html', 
        '"Access your Teambox from this link: __URL__\\n"',
        "HTML text used to send an invitation email from the KCD.")

    prop_set.add_prop('kcd_mail_host', 'mail', "The host name of the outgoing SMTP server.")

    prop_set.add_prop('kcd_mail_sender', '', 
        "The string the sendmail program will use in the From field.\n" +
        "Set this to something representative of your network.")

    prop_set.add_prop('kcd_mail_auth_user', '',
        "User used to authenticate to the SMTP server, if any.")

    prop_set.add_prop('kcd_mail_auth_pwd', '',
        "Password used to authenticate to the SMTP server, if any.")

    prop_set.add_prop('kcd_mail_auth_ssl', 0,
        "True if the connection with the SMTP server must be done over SSL.")

    prop_set.add_prop('kcd_sendmail_path', "/usr/sbin/sendmail",
        "Sendmail program to use. SSTMP is recommended, but all sendmail-compatible\n" +
        "program should work.")

    prop_set.add_prop('kcd_sendmail_timeout', 10,
        "Time we well spend waiting for the sendmail program. If you feel the need to\n"
        + "touch that, then there is probably a problem on your system.")

    prop_set.add_prop('kcd_organizations', 
                      Prop(model = PropModel(cls=ConfigDict, 
                                             cls_args=[long, str],
                                             cls_kwargs={'import_key_call':convert_int_to_long}),
                           doc = 'Organization list. This is used by KCD when it is running in KANP mode.\n'
                           + 'key_id = org_name'))

    prop_set.add_prop('kcd_kfs_mode', 'local', 
        'Location where the KFS files are stored:\n'
        + 'local: the KFS files are stored on the local filesystem.\n'
        + 'samba: the KFS files are stored on a samba filesystem.')

    prop_set.add_prop('kcd_kfs_purge_delay', 1800,
        'Delay before the KFS stale uploaders are purged, in seconds.')

    prop_set.add_prop('kcd_kfs_dir', '/var/teambox/kas/kfs/',
        'Directory where the KFS files are stored when the KFS mode is "local" or\n'
        + '"samba".')

    prop_set.add_prop('kcd_smb_mount_unc', '', 
        'UNC path to the Samba share. ie: //server_name/share_name')

    prop_set.add_prop('kcd_smb_root', '', 
        'UNC path to the samba root directory. ie: /dir1/dir2')

    prop_set.add_prop('kcd_smb_mount_point', '/mnt/kas_kfs', 'Mount point of the Samba share.') 

    prop_set.add_prop('kcd_smb_mount_user', '', 'User of the Samba share.')

    prop_set.add_prop('kcd_smb_mount_pwd', '', 'Password of the Samba share.')

    prop_set.add_prop('kcd_smb_mount_delay', 30, 
        'Delay before the Samba share is remounted after a failure, in seconds.')

    prop_set.add_prop('kcd_smb_check_delay', 30,
        'Delay between checks to validate that the Samba is working, in seconds.')
    
    prop_set.add_prop('kcd_smb_heartbeat_name', "",
        'Name of the file created by kasmond to monitor the Samba share. If this value\n' +
        'is empty, the name of the file is set to the current IP address appended with\n' +
        "'.heartbeat'.")

    prop_set.add_prop('kcd_default_kfs_quota', 10240, 'Default KFS quota, in megabytes.')

    prop_set.add_prop('kcd_db_purge_interval', 900, 'Database purge interval, in seconds.')
    
    # The following KCD fields are set automatically. Do not change their value
    # manually.
    prop_set.add_prop('kcd_kanp_mode', 0, "Support KANP in frontend mode.")
    prop_set.add_prop('kcd_knp_mode', 0, "Support KNP in frontend mode.")
    prop_set.add_prop('kcd_http_mode', 0, "Support HTTP in frontend mode.")
    prop_set.add_prop('kcd_vnc_mode', 0, "Support VNC in frontend mode.")
    prop_set.add_prop('kcd_ssl_cert_path', '/etc/teambox/base/cert.pem', "Path to the SSL certificate, if any.")
    prop_set.add_prop('kcd_ssl_key_path', '/etc/teambox/base/cert_key.pem', "Path to the SSL key, if any.")
    
        
    # Miscellaneous information.
    prop_set.add_prop('production_mode', 0, "True if the server is in production mode.")
    
    
    # Path to the master config file.
    master_file_path = '/etc/teambox/base/master.cfg'
    
    
    def __init__(self):
        AbstractConfigNode.__init__(self)
        
        def ret_true(): return 1
    
        # Dictionary mapping user service names to formatted service names.
        self.user_service_name_dict = odict()
        self.user_service_name_dict["tbxsos"] = "Teambox Sign-On Server"
        self.user_service_name_dict["freemium"] = "Freemium Server"
        self.user_service_name_dict["mas"] = "Main Application Server"
        self.user_service_name_dict["wps"] = "Web Portal Server"
        
        # Dictionary mapping user service names to their runnable function.
        self.user_service_run_dict = odict()
        self.user_service_run_dict["tbxsos"] = self.is_tbxsos_runnable
        self.user_service_run_dict["freemium"] = self.is_freemium_runnable
        self.user_service_run_dict["mas"] = self.is_mas_runnable
        self.user_service_run_dict["wps"] = self.is_wps_runnable
        
        # Dictionary mapping server service names to their runnable function.
        self.server_service_run_dict = odict()
        self.server_service_run_dict["postgres"] = ret_true
        self.server_service_run_dict["apache"] = ret_true
        self.server_service_run_dict["tbxsosd"] = self.must_run_tbxsosd
        self.server_service_run_dict["kcd"] = self.must_run_kcd
        self.server_service_run_dict["kcdnotif"] = self.must_run_kcdnotif
        self.server_service_run_dict["kasmond"] = self.must_run_kasmond
        self.server_service_run_dict["kwsfetcher"] = self.must_run_kwsfetcher
        self.server_service_run_dict["kwmo"] = self.must_run_kwmo
        self.server_service_run_dict["freemium_web"] = self.must_run_freemium_web
        
    # Return true if the following user-visible service configuration is
    # complete.
    def is_tbxsos_config_complete(self):
        return bool(self.kcd_host and os.path.isfile("/usr/bin/tbxsosd"))
    
    def is_freemium_config_complete(self):
        return bool(self.kcd_host and self.is_tbxsos_config_complete())
    
    def is_mas_config_complete(self):
        return bool(self.kcd_host and
                    self.kwmo_host and
                    self.kcd_mail_host and
                    self.kcd_mail_sender and
                    (self.kcd_kfs_mode != "samba" or (self.kcd_smb_mount_unc and self.kcd_smb_mount_user)))

    def is_wps_config_complete(self):
        return bool(self.kcd_host)
                    
    # Return true if the following user-visible services must run in production
    # mode. This is the case if the service and its dependencies are enabled by
    # the user and correctly configured. The return value is independent of
    # whether the server is in production or maintenance mode.
    def is_tbxsos_runnable(self):
        return bool(self.tbxsos_service and self.is_tbxsos_config_complete())
    
    def is_freemium_runnable(self):
        return bool(self.freemium_service and 
                    self.is_freemium_config_complete() and
                    self.is_tbxsos_runnable())
    
    def is_mas_runnable(self):
        return bool(self.mas_service and self.is_mas_config_complete())
    
    def is_wps_runnable(self):
        return bool(self.wps_service and self.is_wps_config_complete())
    
    # Return true if the following Teambox services should be enabled and run.
    # The return value is dependent on whether the server is in production or
    # maintenance mode.
    def must_run_tbxsosd(self):
        return bool(self.production_mode and self.is_tbxsos_runnable())
    
    def must_run_kcd(self):
        return bool(self.production_mode and
                    (self.is_tbxsos_runnable() or
                     self.is_mas_runnable() or
                     self.is_wps_runnable()))
    
    def must_run_kcdnotif(self):
        return bool(self.production_mode and self.is_mas_runnable())
    
    def must_run_kasmond(self):
        return bool(self.production_mode and self.is_mas_runnable())
    
    def must_run_kwsfetcher(self):
        return bool(self.production_mode and self.is_wps_runnable())
    
    def must_run_kwmo(self):
        return bool(self.production_mode and self.is_wps_runnable())
    
    def must_run_freemium_web(self):
        return bool(self.production_mode and self.is_freemium_runnable())
    
    # Normalize the configuration of some services based on the current
    # configuration.
    def normalize_service_config(self):
        self.kcd_kanp_mode = int(self.is_mas_runnable())
        self.kcd_knp_mode = int(self.is_tbxsos_runnable())
        self.kcd_http_mode = int(self.is_freemium_runnable() or self.is_wps_runnable())
        self.kcd_vnc_mode = int(self.is_wps_runnable())
    
    # Return a string describing the first server health issue detected. An
    # empty string is returned if no problem is found.
    def get_health_issue_string(self, service_manager):
    
        # Check that the enabled user services are correctly configured.
        for name in self.user_service_run_dict:
            func = self.user_service_run_dict[name]
            if self[name + "_service"] and not func():
                return "%s is enabled but its configuration is incomplete." % (self.user_service_name_dict[name])
        
        # Check that the server services that should (not) run are (not) enabled
        # and running.
        for name in self.server_service_run_dict:
            func = self.server_service_run_dict[name]
            service = service_manager.get_service(name)
            enabled_flag = service.is_enabled()
            run_status = service.run_status()
            if func():
                if not enabled_flag: return "%s is disabled but it should be enabled" % (name)
                if run_status != 2: return "%s is stopped but it should be running" % (name)
            else:
                if enabled_flag: return "%s is enabled but it should be disabled" % (name)
                if run_status != 0: return "%s is running but it should be stopped" % (name)
         
        return ""
        
    # Load a master config file.
    def load_master_config(self, path=master_file_path, update=False):
        if os.path.isfile(path): content = read_file(path)
        else: content = ""
        if content == "": content = "(())"
        self.load_from_kserialized_obj(eval(content), update=update)

    # Save to a master config file.
    def save_master_config(self, path=master_file_path):
        write_file_atom(path, Dumper().dump_config_to_kserialized_string(self))

    # Read and return the (major, minor) product version tuple contained in the
    # product version file.
    def get_product_version_tuple(self, path="/etc/teambox/product_version"):
        f = open(path, "rb")
        v = f.readline().strip()
        f.close()
        match = re.match("(\d+).(\d+)", v)
        if not match: raise Exception("cannot read valid version number from %s" % (path))
        return (int(match.group(1)), int(match.group(2)))
        
    # Return true of the root password is locked.
    def is_root_pwd_locked(self):
        out = get_cmd_output(["passwd", "-S", "root"])
        sout = out.split(" ")
        return sout[1] == 'L'
    
    # Return a tuple containing the hostname and the domain extracted from the
    # fully qualified domain name specified.
    def split_fqdn(self, host):
        if not isinstance(host, basestring): raise Exception("invalid host string")
        host = host.strip()
        if host.find(' ') != -1 or host.find('..') != -1: raise Exception("host is not valid")
        host_array = host.split('.')
        hostname = host_array[0]
        if len(host_array) > 1: domain = '.'.join(host_array[1:])
        else: domain = ''
        return (hostname, domain)
    
    # Return the fully qualified domain name.
    def get_fqdn(self):
        s = self.hostname
        if self.domain: s += "." + self.domain
        return s
    
    # Set the fully qualified domain name.
    def set_host(self, service_manager, host=None, output_stream=None):
        
        # Split the FQDN.
        (self.hostname, self.domain) = self.split_fqdn(host)
        
        # Update the master configuration file.
        self.save_master_config()

        # Write network config.
        self.write_network_config()

        # Reload the hostname.
        service_manager.reload_hostname()
 
    # Set the root password. If None is specified, the current administration
    # password is used.
    def set_root_pwd(self, pwd=None):
        if pwd == None: pwd = self.admin_pwd
        if pwd == "": get_cmd_output(["passwd", "-l", "root"])
        else: get_cmd_output(["chpasswd"], input_str="root:" + pwd)
    
    # Set the administrator password. If None is specified, the current
    # administration password is used.
    def set_admin_pwd(self, pwd=None):
        if pwd == None: pwd = self.admin_pwd
        else: self.admin_pwd = pwd
        
        # Update the password in the administration password file.
        write_file_atom('/etc/teambox/base/admin_pwd', pwd + "\n")
        
        # Update the password in postgres.
        get_cmd_output(["psql", "-d", "template1", "-c",
                        "ALTER ROLE external WITH PASSWORD %s" % (escape_string(pwd))])
                        
        # Update the password in tbxsosd.
        self.change_key_tbxsosd_config("/etc/teambox/tbxsosd/web.conf", "server.password", pwd)
        
        # Update the password in the master configuration file. Do this last for
        # consistency.
        self.save_master_config()
    
    # Enable/disable service services according to their runnable state.
    def set_server_service_enabled_state(self, service_manager, force_flag):
        for name in self.server_service_run_dict:
            func = self.server_service_run_dict[name]
            service = service_manager.get_service(name)
            enable_flag = func()
            if force_flag or bool(service.is_enabled()) != bool(enable_flag): service.set_enabled(enable_flag)
    
    # Switch mode helper.
    def _switch_mode_helper(self, service_manager, production_mode_flag, force_flag, output_stream):
        
        # Update the configuration.
        self.production_mode = int(production_mode_flag)
        self.normalize_service_config()
        self.save_master_config()
        self.write_service_config()
        self.write_network_config()
        
        # Reload the hostname and the firewall rules.
        service_manager.reload_hostname()
        service_manager.reload_firewall_rules()
        
        # Enable/disable the services and restart them.
        self.set_server_service_enabled_state(service_manager, force_flag)
        service_manager.restart_services(force_flag, output_stream)
        
        # Reload Apache configuration.
        service_manager.get_service("apache").reload_config()
    
    # Switch to production mode.
    def switch_to_production_mode(self, service_manager, force_flag=0, output_stream=None):
        self._switch_mode_helper(service_manager, 1, force_flag, output_stream)
    
    # Switch to maintenance mode.
    def switch_to_maintenance_mode(self, service_manager, force_flag=0, output_stream=None):
        self._switch_mode_helper(service_manager, 0, force_flag, output_stream)
    
    # Change a key in a tbxsosd-style configuration file.
    def change_key_tbxsosd_config(self, file_path, key, val):
        out_lines = []
        changed_line = '%s = "%s";' % (key, val)
        found = 0
        for line in read_file(file_path).split("\n"):
            if line.strip() == "": continue
            if line.startswith(key):
                line = changed_line
                found = 1
            out_lines.append(line)
        if not found: out_lines.append(changed_line)
        write_file_atom(file_path, "\n".join(out_lines) + "\n")
    
    # Bind an INI file to this node and define some methods for convenience.
    def bind_ini_file(self):
        node = self
        
        class BoundIniFile(KIniFile):
            def __init__(self):
                KIniFile.__init__(self)
                self.node = node
            
            def prop_key(self, section, key, prop_name):
                self.set(section, key, self.node[prop_name], self.node.prop_set[prop_name].doc)
             
            def prop_section(self, section, prop_name):
                self.add_section(section, doc=self.node.prop_set[prop_name].doc)
                
        return BoundIniFile()
    
    # Write configuration to /etc/teambox/tbxsosd/web.conf.
    def update_tbxsosd_web_conf(self, file_path="/etc/teambox/tbxsosd/web.conf"):
        self.change_key_tbxsosd_config(file_path, "server.listen_on", "0.0.0.0:5000")
        self.change_key_tbxsosd_config(file_path, "server.ssl_listen_on", "")
        self.change_key_tbxsosd_config(file_path, "server.kas_address", self.kcd_host)
        self.change_key_tbxsosd_config(file_path, "server.kas_port", 443)
        
    # Write configuration to kcd.ini.
    def write_kcd_ini(self, file_path='/etc/teambox/kcd/kcd.ini'):
        ini_file = self.bind_ini_file()

        # Write config section.
        ini_file.add_section('config')
        for name in ['kanp_mode', 'knp_mode', 'http_mode', 'vnc_mode', 'listen_addr',
                     'listen_port', 'ssl_cert_path', 'ssl_key_path', 'kmod_binary_path',
                     'kmod_db_path', 'vnc_cred_path', 'web_port', 'web_link', 
                     'invite_mail_kcd_html', 'mail_host', 'mail_sender', 'mail_auth_user',
                     'mail_auth_pwd', 'mail_auth_ssl', 'sendmail_path', 'sendmail_timeout']:
            ini_file.prop_key('config', name, 'kcd_' + name)
        ini_file.prop_key('config', 'kcd_host', 'kcd_host')
        ini_file.prop_key('config','web_host', 'kwmo_host')

        # Write organizations.
        ini_file.prop_section('organizations', 'kcd_organizations')
        for key, org in self.kcd_organizations.items():
            ini_file.set('organizations', str(key), org)

        write_file_atom(file_path, ini_file.write_to_string())
        
        # Restriction hack.
        restriction_path = "/etc/freemium"
        if self.kcd_enforce_restriction: write_file(restriction_path, "")
        else: delete_file(restriction_path)
    
    # Write configuration to kfs.ini.
    def write_kfs_ini(self, file_path='/etc/teambox/kcd/kfs.ini'):
        ini_file = self.bind_ini_file()
        ini_file.add_section('config')
        for name in ['kfs_mode', 'kfs_purge_delay', 'kfs_dir', 'smb_mount_unc', 
                     'smb_mount_point', 'smb_mount_user', 'smb_mount_pwd', 
                     'smb_mount_delay', 'smb_check_delay', 'smb_heartbeat_name',
                     'default_kfs_quota']:
            ini_file.prop_key('config', name, 'kcd_' + name)

        # Write file.
        write_file_atom(file_path, ini_file.write_to_string())
    
    # Write configuration to /etc/ssmtp/ssmtp.conf.
    def write_ssmtp_conf_file(self, path="/etc/ssmtp/ssmtp.conf"):
        s = ""
        s += "root=postmaster\n"
        s += "hostname=%s\n" % (self.kcd_host)
        s += "mailhub=%s\n" % (self.kcd_mail_host)
        if self.kcd_mail_auth_user: s += "AuthUser=%s\n" % (self.kcd_mail_auth_user)
        if self.kcd_mail_auth_pwd: s += "AuthPass=%s\n" % (self.kcd_mail_auth_pwd)
        if self.kcd_mail_auth_ssl: s += "UseSTARTTLS=Yes\n"
        s += "FromLineOverride=Yes\n"
        write_file_atom(path, s)
   
    # Write the hostname in /etc/hostname.
    def write_etc_hostname_file(self, path="/etc/hostname"):
        write_file(path, self.hostname + "\n")
    
    # Write the hosts in in /etc/hosts.
    def write_etc_hosts_file(self, path="/etc/hosts"):
        s = "127.0.0.1\tlocalhost"
        if self.hostname != "localhost":
            s += " " + self.hostname
            if self.domain: s += " %s.%s" % (self.hostname, self.domain)
        s += "\n"
        write_file(path, s)
    
    # Write configuration to /etc/network/interfaces.
    def write_etc_network_file(self):
        s = ""
        s += "auto lo eth0\n"
        s += "iface lo inet loopback\n"
        
        if self.eth0.method == "dhcp":
            s += "iface eth0 inet dhcp\n"
        else:
            s += "iface eth0 inet static\n"
            s += "\taddress " + self.eth0.ip + "\n"
            s += "\tnetmask " + self.eth0.netmask + "\n"
            
            # We have to add the gateway in this fashion to support a gateway on
            # a different subnet.
            s += "up route add -host " + self.eth0.gateway + " eth0\n"
            s += "up route add default gw " + self.eth0.gateway + "\n"
        s += "\n"
        
        write_file_atom("/etc/network/interfaces", s)
    
    # Write configuration to /etc/resolv.conf file, if necessary.
    def write_etc_resolv_file(self):
        if self.eth0.method != "static": return
        s = ""
        if self.domain: s += "search " + self.domain + "\ndomain " + self.domain + "\n"
        for addr in self.dns_addr_list:
            s += "nameserver " + addr + "\n"
        write_file_atom("/etc/resolv.conf", s)
    
    # Write configuration to /etc/ssh/sshd_config.
    def write_sshd_config_file(self):
        stock_sshd_config = "/etc/teambox/base-config/sshd_config"
        s = ""
        s += "# WARNING: THIS FILE IS AUTO-GENERATED.\n\n"
        s += read_file(stock_sshd_config)
        for line in self.sshd_line_list: s += line + "\n"
        write_file_atom("/etc/ssh/sshd_config", s)
    
    # Write the content of /etc/teambox/base/iptables.rules.
    def write_iptables_config_file(self):
        s = ""
        
        # This is the filter table.
        s += "*filter\n"
        
        # Drop everything by default for the forward tables. Allow everything by
        # default for the input and output table.
        s += ":INPUT ACCEPT\n"
        s += ":FORWARD DROP\n"
        s += ":OUTPUT ACCEPT\n"
        
        # Allow all loopback traffic.
        s += "-A INPUT -i lo -j ACCEPT\n"
        
        # In maintenance mode, deny remote access to port 443 and 5432.
        if not self.production_mode:
            s += "-A INPUT -p tcp -m tcp --dport 443 -j REJECT\n"
            s += "-A INPUT -p tcp -m tcp --dport 5432 -j REJECT\n"
        
        # Public ports. Port 22 is protected by sshd_config that has AllowUsers
        # clauses.
        s += "-A INPUT -p tcp -m tcp --dport 22 -j ACCEPT\n"
        s += "-A INPUT -p tcp -m tcp --dport 443 -j ACCEPT\n"
        
        # Allow access to all ports to the specified addresses.
        for line in self.all_port_addr_list:
            s += "-A INPUT -s %s -p tcp -m tcp -j ACCEPT\n" % (line)
        
        # Allow access to configuration ports to the specified addresses.
        for line in self.config_port_addr_list:
            s += "-A INPUT -s %s -p tcp -m tcp --dport 9000:9001 -j ACCEPT\n" % (line)
        
        # Accept incoming pings.
        s += "-A INPUT -p icmp -m icmp --icmp-type 8 -m state --state NEW -j ACCEPT\n"
        
        # Reject IDENT packets.
        s += "-A INPUT -p tcp -m tcp --dport 113 -j REJECT --reject-with icmp-port-unreachable\n"
        s += "-A OUTPUT -p tcp -m tcp --dport 113 -j REJECT --reject-with icmp-port-unreachable\n"
        
        # Allow packets from connections that we have established.
        s += "-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT\n"
        
        # Reject everything else. Do not set the input policy to DROP, this is
        # hard to debug.
        s += "-A INPUT -j REJECT\n"
        
        # Commit the changes.
        s += "COMMIT\n"
        
        write_file_atom("/etc/teambox/base/iptables.rules", s)
    
    # Write the service configuration.
    def write_service_config(self):
        self.update_tbxsosd_web_conf()
        self.write_kcd_ini()
        self.write_kfs_ini()
        self.write_ssmtp_conf_file()
   
    # Write the network configuration.
    def write_network_config(self):
        self.write_etc_hostname_file()
        self.write_etc_hosts_file()
        self.write_etc_network_file()
        self.write_etc_resolv_file()
        self.write_sshd_config_file()
        self.write_iptables_config_file()

