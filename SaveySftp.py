from fabric import Connection
from fabric import __version__
from PyQt5.QtCore import QRegExp
import os

"""
HOST='freezer'
USER='pablo'
PORT=2222
PATH='/RAID1_HOME/_AUTOMATED_/10.0.0.17/'
"""

# Globals
globals()['lib_version'] = "SaveySftp 0.001"


class SaveySftp():

    def version():
        return globals()['lib_version']

    def __init__(self, name):
        self.name = name
        self.connected = False

        print(f"SaveySftp instance named: {name} created.")

        # Host variables

        self.host = None
        self.user = None
        self.port = None
        self.host_uname = None
        self.host_ssh_ver = None
        self.error = None

        # Get Client lib info
        self.client_ssh_ver = "Fabric " + __version__

    def define_con(self, _host, _user, _port=22):
        self.host=_host
        self.user=_user
        self.port=_port

    def con(self):
        try:
            # Get $HOME environment variable
            home_dir_path = os.environ["HOME"]
            # Do Connect
            c = Connection(
                    self.host,
                    self.user,
                    self.port,
                    connect_timeout=5,
                    connect_kwargs = {
                        "key_filename": home_dir_path+"/.ssh/id_rsa.pub",                        
                        },
                    )
            # Attach instance
            self.c = c

            # Get Server info
            res = c.run("uname -a", hide='both')
            if res.ok:
                self.host_uname = res.stdout
            else:
                self.host_uname = "ERROR"

            res = c.run("ssh -V", hide='both')
            if res.ok:
                self.host_ssh_ver = res.stderr
            else:
                self.host_ssh_ver = "ERROR"

            # New SFTP Client
            s = c.sftp()
            self.s = s

            if s is not None:
                # Reaching here means ok
                self.connected = True
        except Exception as err:
            print(f"SSH/SFTP ERROR: {err}")
            self.connected = False

            # Check for known errors
            #
            #while ((pos = err_rx.indexIn(err, pos)) != -1) { }
            err_str_arr = ["Unable to Connect"]
            for err_str in err_str_arr:
                err_rx = QRegExp("($err_str)")
                if err_rx.cap(1) is not None:
                    self.error = err_str
                    break

            print(f"__file__@con(): self.error={self.error}")

    def ls_path(self, _path=None):
        if self.is_connected():
            if _path is None:
                _path = self.path
            result = self.s.listdir(_path)
            self.result = result

    def file_info(self, _path):
        if self.is_connected():
            res = self.c.run(f"identify {_path}", hide='both')
            if res.ok:
                self.file_ident = res.stdout
            else:
                self.file_ident = "ERROR"
        #emit to MW that info is ready
        return self.file_ident

    def remove(self, _path,):
        try:
            if self.is_connected():
                self.s.remove(_path)
        except Exception as err:
            print(f"SSH/SFTP ERROR: {err}")

    def get(self, _path, _localpath):
        try:
            if self.is_connected():
                self.s.get(_path, _localpath)
        except Exception as err:
            print(f"SSH/SFTP ERROR: {err}")


    def set_path(self, _path):
        self.path = _path

    def is_connected(self):
        return self.c.is_connected

    def close_con(self):
        if self.is_connected():
            try:
                if self.s is not None:
                    self.s.close()
                    # reset values
                    self.host_uname = "Disconnected"
                    self.host_ssh_ver = "Disconnected"
                else:
                    print("SFTP object not present")
            except Exception as err:
                print(f"SSH/SFTP ERROR: {err}")
            # Redundant but still proper
            self.c.close()
            print(f"SSH/SFTP connection: {self.name} terminated.")
        else:
            print(f"SSH/SFTP connection: {self.name} was already terminated.")
