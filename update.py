try:
    from urllib.request import urlretrieve, urlopen
except:
    from urllib import urlretrieve
    from urllib2 import urlopen
from subprocess import Popen
from os.path import basename
from sys import exit, argv

DETACHED_PROCESS = 0x8
executable = argv[0]

def can_update(remote_url):
    try:
        return (not sys.argv[0].endswith('python.exe')
                and urlopen(remote_url).code < 400)
    except:
        return False

def update_and_restart(remote_url, auto_exit=False):
    assert can_update(remote_url)

    filename = basename(remote_url)
    temporary_file = filename + '.new'
    urlretrieve(remote_url, temporary_file)

    open('update.bat', 'w').write("""
timeout 1 /nobreak
del {current_file}
rename {temporary_file} {new_file}
start {new_file}
del update.bat
    """.format(current_file=executable,
               temporary_file=temporary_file,
               new_file=filename))

    logfile = open('log.txt', 'w')
    Popen('update.bat', creationflags=DETACHED_PROCESS, shell=True, stdout=logfile, stderr=logfile)

    if auto_exit:
        exit('restarting to apply updates')
