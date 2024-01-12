'''
this file aids in backup, copy and restore of container over network using ssh utility.
The migrate and restore script file is provided with docker setup and container API project
'''
import paramiko
from scp import SCPClient

def sshTest():
    """_summary_
    Test SSH connection to the remote server
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("192.168.122.210", 22, 'ubuntu', 'ubuntu')
    ssh.exec_command('ls -l')
    ssh.exec_command('touch testssh.txt')

def sshmigrate(srcIP, id):
    """_summary_
    This function will take source IP address as input parameter and use it to connect to that machine via
    SSH and then fetches Docker Container details from that system and copies them onto local system.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(srcIP, 22, 'ubuntu', 'ubuntu')
    ssh.exec_command(f'python3 migrateVictim.py {id}')

def sshrestore(destIp):
    """_summary_
    This function takes destination IP address as an argument and uses it to make SSH connection to the given
    IP Address. It then calls the `restoreContainer.sh` shell script which does the
    restoration of copied containers on the specified machine.
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(destIp, 22, 'ubuntu', 'ubuntu')
    ssh.exec_command('python3 restoreimage.py')

def createSSHClient(server, port, user, password):
    """_summary_
    Create an instance of SSH client for given server information
    """
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def sshcopy_(server1, server2, port, user, password):
    ssh = createSSHClient(server1, port, user, password)
    scp = SCPClient(ssh.get_transport())
    scp.get('ubuntu-test.img')
    ssh = createSSHClient(server2, port, user, password)
    scp = SCPClient(ssh.get_transport())
    scp.put('ubuntu-test.img')

def sshcopy(server1, server2, port, user, password):
    """_summary_
    Copies docker images between two servers using scp protocol over ssh
    """
    ssh = createSSHClient(server1, port, user, password)
    scp = SCPClient(ssh.get_transport())
    scp.get('/home/ubuntu/images/ubuntu-test.img')
    print("got")

    ssh = createSSHClient(server2, port, user, password)
    scp = SCPClient(ssh.get_transport())
    scp.put('ubuntu-test.img')
    ssh.exec_command('sudo mv ubuntu-test.img /home/ubuntu/images/')

if __name__ == '__main__':
    pass



