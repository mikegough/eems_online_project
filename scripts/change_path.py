import os
#search = "/home/consbio/webapps/eems/" 
#replace =  "/home/mike/apps/eems-online/"
search =  "/home/mike/apps/eems-online/"
replace = "F:/Projects2/EEMS_Online/tasks/web_applications/eems_online_django/"
for dname, dirs, files in os.walk("./"):
    for fname in files:
        fpath = os.path.join(dname, fname)
	if ".mpt" in fpath: 
		print(fpath)
		with open(fpath) as f:
		    s = f.read()
		s = s.replace(search, replace)
		with open(fpath, "w") as f:
		    f.write(s)
