from __future__ import with_statement
from fabric.api import local, settings, sudo, lcd
from fabric.utils import abort
from fabric.contrib.console import confirm

def run():
    local("python manage.py runserver")

def prepare_deploy():
    local("./manage.py test Tanalyzer")
    local("git add -p && git commit")
    local("git push")

def configure():
    local("python manage.py syncdb")
    local("python manage.py loaddata data_base_bz.json")

def install(machine="mac"):
    
    local("touch mastertopics.txt settings_local.py")

    if machine == "mac":

        egg_base_path = "/Library/Python/2.7/site-packages/"
        print "Need to install homebrew"

        brew_wrapper("wget")
        brew_wrapper("mysql")

    elif machine == "ubuntu":

        egg_base_path = "/usr/local/lib/python2.7/site-packages/"
        local("sudo apt-get install mysql-server python-django python-mysqldb python-numpy python2.7-dev apparmor-utils libapache2-mod-wsgi")


    local("sudo pip install beautifulsoup4")
    local("sudo pip install lxml")

    #Django
    django_egg = egg_base_path+'Django-1.4-py2.7.egg-info'
    django_url = 'https://www.djangoproject.com/download/1.4/tarball/'
    python_install_from_url(django_url,"Django-1.4", django_egg)

    #MySql-Python
    mysql_py_client_egg = egg_base_path+"MySQL_python-1.2.3-py2.7-macosx-10.7-intel.egg"
    mysql_py_client_url = "http://ufpr.dl.sourceforge.net/project/mysql-python/mysql-python/1.2.3/MySQL-python-1.2.3.tar.gz"
    python_install_from_url(mysql_py_client_url,"MySQL-python-1.2.3", mysql_py_client_egg)

    #Dajax
    dajax_egg = egg_base_path+"django_dajax-0.8.4-py2.7.egg-info"
    dajax_url = "https://github.com/downloads/jorgebastida/django-dajax/django-dajax-0.8.4.tar.gz"
    python_install_from_url(dajax_url,"django-dajax-0.8.4",dajax_egg)

    #DajaxIce
    dajax_ice_egg = egg_base_path+"django_dajaxice-0.2-py2.7.egg-info"
    dajax_ice_url = "https://github.com/downloads/jorgebastida/django-dajaxice/django-dajaxice-0.2.tar.gz"
    python_install_from_url(dajax_ice_url,"django-dajaxice-0.2",dajax_ice_egg)

    #DeltaLDA
    delta_lda_egg = egg_base_path+"deltaLDA-0.1.1-py2.7.egg-info"
    delta_lda_url = "http://pages.cs.wisc.edu/~andrzeje/research/deltaLDA.tgz"
    python_install_from_url(delta_lda_url,"deltaLDA-0.1.1",delta_lda_egg)



def python_install_from_url(url,file_name, egg):

    with settings(warn_only=True):
        test_result = local("test -f %s" % egg, capture = True)

    if test_result.failed:
        result = local("wget "+url+" -O "+file_name+".tar.gz", capture = True)
        if result.success:

            local("tar xzvf "+file_name+".tar.gz")
            with lcd(file_name):
                local("sudo python setup.py install --record "+file_name+"_install.log")

            local("sudo rm -rf "+file_name+"")
            local("rm -f "+file_name+".tar.gz")
    else:
        print file_name+" already installed"

def brew_wrapper(target):

    with settings(warn_only=True):
        response = local("brew install "+target, capture=True)
        if response.failed: 
            if "already" in str(response):
                print str(response)
            else:
                abort(str(response))
