#!/bin/sh

# Compat krun module for systems with an old kpython.

from krun import *

try:
    __junk = krun_join_with_whitespace
except:
    # Helper function for get_cmd_output() and show_cmd_output(). Join a list of
    # strings with whitespaces.
    def krun_join_with_whitespace(l):
        res = ""
        for e in l:
            if res != "": res += " "
            res += e
        return res

try:
    __junk = krun_adjust_arg_list
except:
    # Helper function for get_cmd_output() and show_cmd_output(). Return a list of
    # strings or a single string depending on the value of 'shell_flag'.
    def krun_adjust_arg_list(arg_list, shell_flag):
        args = arg_list
        if shell_flag and type(arg_list) == list: args = krun_join_with_whitespace(arg_list)
        elif not shell_flag and type(arg_list) == str: args = arg_list.split()
        return args


try:
    __junk = show_cmd_output
except:
    # This function is similar to get_cmd_output(), with the difference that the
    # output of the command (stdout, stderr) is not redirected. The function throws
    # an exception if the command fails if requested.
    def show_cmd_output(arg_list, ignore_error=0, shell_flag=0):
        args = krun_adjust_arg_list(arg_list, shell_flag)

        if type(arg_list) == str: cmd_name = arg_list.split()[0]
        else: cmd_name = arg_list[0]

        try:
            proc = Popen(args=args, shell=shell_flag)
            proc.communicate()
            if proc.returncode != 0 and not ignore_error: raise Exception("command " + cmd_name + " failed")

        except Exception, e:
            if not ignore_error: raise Exception("command " + cmd_name + " failed")



