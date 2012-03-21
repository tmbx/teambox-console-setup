# Reboot job to add hard drives to the LVM root.
#  
# author: François-Denis Gonthier

@reboot root /usr/bin/lvmsetup
