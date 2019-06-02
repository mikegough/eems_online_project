cd /home/consbio/webapps/celery_vm_app
source bin/activate
supervisorctl stop all
ps -A | grep supervisor | awk '{print $1}' | xargs kill
supervisord
/home/consbio/webapps/eems/apache2/bin/restart
