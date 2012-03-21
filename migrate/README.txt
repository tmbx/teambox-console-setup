The 'kasmig' script is used to backup, migrate and consolidate servers.

To backup/migrate/consolidate a server, issue the command 'kasmig pull
servername reposname'. This will pull the data from 'servername' and place it
in the local directory /var/teambox/kasmig/reposname/. Make sure you have SSH
keys in place for the root user.

You can select which components to pull with the '-c' switches.

To migrate a server, deploy a new standard unconfigured Teambox server. Make
sure tbxsosd-tbxsos is installed if you plan on using it. Then, issue the
command 'kasmig push servername reposname' to push the data pulled from the old
servers to the new server. You have to restart the network interfaces and put
the server in production mode manually.

To consolidate several servers into a single server, pull the data from the
decommissioned servers then push that data to the consolidated server using the
'-c' switches.

