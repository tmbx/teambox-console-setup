This repository contains a script to transform a base installation into a
virtual machine containing a KAS. Follow the following steps:

1) Create a fresh virtual machine.
   Other linux, disk 40GB, don't allocate now, don't split in 2GB files.

2) Install the Teambox platform from the bare ISO on the virtual machine.
   To boot from the ISO, edit the virtual machine settings, click on the CDROM
   device, and click on "Use ISO image".
   Set the password you want as the root password, it will be cleared.
   Once the installation is completed, shut down the machine.
   In vmware console, edit the virtual machine settings.
   Remove the floppy.
   In the CDROM device tab, deselect "Connect at power on", and select
   "use a physical drive".
   In the memory tab, set the RAM to 1024MB.
   You may want to take a snapshot at this point.

3) Update the 'config.ini' file in this directory.

4) Execute the 'run' program in this directory.
   NOTE: you need to have the 'kpython' package installed.

5) Pray that it works (optional).

6) Power down the machine.
   Do *NOT* reboot the machine, otherwise the various keys and certificates 
   used on the machine will be inappropriately regenerated.
   You *MUST* remove the snapshot using the *vmware console*, if there is one.

7) Login on the physical machine hosting the VM.
   Go in the directory containing the VM.
   Delete every file but the .vmx and the .vmdk file.
   The name of the files without the extension should be "Kcd" or "Kwmo".
   Edit the .vmx file:
     If necessary, change the value of "scsi0:0.fileName" to the name of the
     .vmdk file
     If necessary, change the value of "displayName" to the "KcdVM" or "KwmoVM".
 
8) Convert the VMware Server machines to VMware ESX.
   Start VMware Converter and click on "Convert Machine".
   Select "other" as Source type.
   Choose the .vmx image to convert.
   Select "virtual appliance" as Destination type.
   Name the machine appropriately.
   When asked to supply to the machine information, provide the version number.
   Leave "Folder of files" as destination format, don't create manifest.
   Start the conversion.

