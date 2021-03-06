#!/bin/python
import unittest
import pdb
import os
import tarfile
import utilpack
import urllib
import sys
import tarfile
import re
import md5
import string
from pdb import set_trace as stra
import shutil


global dostest

class TestCygApt(unittest.TestCase):

    def setUp(self):
        # Verbose: echos cyg-apt commands and results
        self.v =  ("-vv" in sys.argv)
        self.dostest = dostest
        self.rc_regex = re.compile("^\s*(\w+)\s*=\s*(.*)\s*$")
        self.rc_options = ['ROOT', 'mirror', 'cache', 'setup_ini', 'distname', 'barred']
        self.package_name = "testpkg"
        self.package_name_2 = "testpkg-lib"
        self.package_search_regex = "testpkg(-lib)?"
        self.package_find_regex = "/usr/bin/.estpkg"
        self.relname = "release-2"
        self.cyg_apt_rc_file = ".cyg-apt"
        self.tarname = "testpkg-0.0.1-0.tar.bz2"
        self.tarname_2 = "testpkg-0.0.2-0.tar.bz2"
        self.tarpath = "release-2/testpkg/"                
        self.sourcename = "testpkg-0.0.1-0"
        self.sourcemarker = "mini_mirror/testpkg/build/root/usr/bin/testpkg.exe"
        self.source_unpack_marker = "testpkg-0.0.1-0/usr/bin/testpkg.exe"
        self.version_2_marker = "/etc/ver2_marker"
        self.testpkg_lib_marker = "/usr/lib/testpkg-lib.marker"
        self.pre_remove_marker = "/usr/share/doc/testpkg/README"
        self.postinstall_marker = self.pre_remove_marker
        self.post_remove_marker = "/usr/share/doc/testpkg"
        self.post_install_script = "/etc/postinstall/testpkg.sh"
        self.post_install_script_done = \
            "/etc/postinstall/testpkg.sh.done"
        self.pre_remove_script = "/etc/preremove/testpkg.sh"
        self.post_remove_script = "/etc/postremove/testpkg.sh"
        self.pre_remove_script_done = "/etc/preremove/testpkg.sh.done"
        self.post_remove_script_done = "/etc/postremove/testpkg.sh.done"
        self.tarfile = "mini_mirror/testpkg/build/release-2/testpkg/" +\
            self.tarname
        self.tarfile_2 = "mini_mirror/testpkg/build/release-2/testpkg/" +\
            self.tarname_2
        self.build_setup_ini = "mini_mirror/setup-2.ini"
        self.init_from_dot_cyg_apt()
        self.expected_ballpath = "%s/%s/%s/%s/%s" % \
            (self.opts["cache"],\
            self.mirror_esc,\
            self.relname,\
            self.package_name,\
            self.tarname)
        self.ver = "0.0.1-0"

            
        setup_rc_filename  = "/etc/setup/setup.rc"
        old_last_mirror = "/etc/setup/last-mirror"
        old_last_cache = "/etc/setup/last-cache"
        
        if (os.path.exists(setup_rc_filename)):
            setup_rc = file(setup_rc_filename).readlines()
            last_cache = None
            last_mirror = None
            for i in range(0, (len(setup_rc) -1)):
                if "last-cache" in setup_rc[i]:
                    last_cache = setup_rc[i+1].strip()
                if "last-mirror" in setup_rc[i]:
                    last_mirror = setup_rc[i+1].strip()
            last_cache = os.popen("cygpath -au \"" + last_cache + "\"").read().strip()
            self.last_cache = last_cache
            self.last_mirror = last_mirror
        elif (os.path.exists(old_last_mirror) and\
            os.path.exists(old_last_cache)):
            self.last_mirror = file(old_last_mirror).read().strip()
            self.last_cache = file(old_last_cache).read().strip()
            self.last_cache = self.cygpath(self.last_cache)
        else:
            print "Can't test without access to last-mirror last-cache, exiting."
            self.assert_(False)

        self.cwd_cyg_apt = ".cyg-apt" 
        self.home_cyg_apt = os.environ['HOME'] + "/.cyg-apt"            
            
        if os.path.exists(self.cwd_cyg_apt):
            self.cwd_cyg_apt_bak = self.cwd_cyg_apt + ".bak"        
            utilpack.popen_ext\
                ("cp %s %s" % (self.cwd_cyg_apt, self.cwd_cyg_apt_bak))
        else:
            self.cwd_cyg_apt = None
        if os.path.exists(self.home_cyg_apt):
            self.home_cyg_apt_bak = self.home_cyg_apt + ".bak"
            utilpack.popen_ext("cp %s %s" % (self.home_cyg_apt, self.home_cyg_apt_bak))
        else:
            self.home_cyg_apt_bak = None
            
        found = False
        mountout = utilpack.popen_ext("mount")[0].split("\n")
        for l in mountout:
            if "on / " in l:
                l = l.split()[0]
                l = l.replace(":", "")
                self.root = "/" + l + "/"
                found = True
                break
        self.assert_(found)
        self.symlink_location = "/usr/bin/link_to_testpkg"
        self.hard_link_location = "/usr/bin/hardlink_to_testpkg"
        instout = self.launchtest("gpg --import cyg-apt-test-pub.gpg")
        instout = self.launchtest\
            ("gpg --allow-secret-key-import --import cyg-apt-test-sec.gpg")
        

    def init_from_dot_cyg_apt(self):
        self.opts = {}
        rc = file(self.cyg_apt_rc_file).readlines()
        for i in rc:
            result = self.rc_regex.search(i)
            if result:
                k = result.group(1)
                v = result.group(2)
                if k in self.rc_options:
                    self.opts[k] = eval(v)
        self.mirror_esc = urllib.quote(self.opts["mirror"], "").lower()


    def cygpath(self, path):
        path = path.replace("\\", "/")
        if len(path) == 3:
            if path[1] == ":":
                path = "/" + path[0].lower()
        elif len(path) > 1:        
            if path[1] == ":":
                path = "/" + path[0].lower() + path[2:]
        return path
    
    
    def do_testsetup(self):
        setup_out = utilpack.popen_ext("./cyg-apt setup", self.v)[1]
        self.assert_fyes(self.home_cyg_apt)
        cyg_apt_rc = file(self.home_cyg_apt, "r").readlines()
        rc_dict = {}
        for l in cyg_apt_rc:
            result = self.rc_regex.search(l)
            if result:
                k = result.group(1)
                v = result.group(2)
                rc_dict[k] = eval(v)
        self.assert_(rc_dict["mirror"] == self.last_mirror)
        self.assert_(rc_dict["cache"] == self.last_cache)


    def testsetup(self):
        if self.dostest:
            setupout = self.launchtest("./cyg-apt setup", self.v)[0]
            self.assert_(" setup outside Cygwin not supported" in setupout)
            return
        if os.path.exists(self.cwd_cyg_apt):        
            self.assert_fyes(self.cwd_cyg_apt_bak)
            utilpack.popen_ext("rm %s" % self.cwd_cyg_apt)
        if os.path.exists(self.home_cyg_apt):
            utilpack.popen_ext("rm %s" % self.home_cyg_apt)
        try:
            self.do_testsetup()
        finally:
            if os.path.exists(self.cwd_cyg_apt_bak):
                out = utilpack.popen_ext("cp %s %s" % (self.cwd_cyg_apt_bak, self.cwd_cyg_apt))[0]
                if not out:
                    utilpack.popen_ext("rm %s" % self.cwd_cyg_apt_bak)
            if self.home_cyg_apt_bak and os.path.exists(self.home_cyg_apt_bak):
                out = utilpack.popen_ext("cp %s %s" % (self.home_cyg_apt_bak, self.home_cyg_apt))[0]
                if not out:
                    utilpack.popen_ext("rm %s" % self.home_cyg_apt_bak)
    
    
    def testball(self):
        ballpath = self.launchtest\
            ("./cyg-apt ball " + self.package_name, self.v)[0]
        ballpath = ballpath.strip()
        # The tarball location is:
        # cache + mirror + releasename + packagename + tarfile_name
        if self.dostest:
            ballpath = os.popen("cygpath " + ballpath).read().strip()
        self.assert_(self.expected_ballpath == ballpath)
        
        
    def testdownload(self):
        # First test ability to recognise package that is already 
        #present: download twice to make sure it is there on the second 
        #attempt: independent unittests.
        download_out = self.launchtest\
            ("./cyg-apt download " + self.package_name, self.v)[0]
        download_out = self.launchtest\
            ("./cyg-apt download " + self.package_name, self.v)[0]
        download_out = download_out.split("\n")
        download_out = [x for x in download_out if x != ""]
        self.assert_(download_out[-1] == download_out[-2])
        self.assert_fyes(self.expected_ballpath)
        
        # Second test: test we can recognise a package is 
        # not present in the cache and download it.
        os.remove(self.expected_ballpath)
        self.assert_fno(self.expected_ballpath)
        download_out = self.launchtest\
            ("./cyg-apt download " + self.package_name, self.v)[0]
        download_out = download_out.split("\n")
        download_out = [x for x in download_out if x != ""]
        self.assert_(download_out[-1] == download_out[-2])
        self.assert_fyes(self.expected_ballpath)
        
    
    def testfilelist(self):
        self.launchtest("./cyg-apt install " + self.package_name, self.v)[0]
        filelistout = self.launchtest\
           ("./cyg-apt filelist " + self.package_name, self.v)[0]
        filelistout = filelistout.split()
        if tarfile.is_tarfile(self.expected_ballpath):
            input_tarfile = tarfile.open(self.expected_ballpath)
            contents = input_tarfile.getnames()
            for x,y in zip(filelistout, contents):
                self.assert_(x == y)            
        else:
            # Has test-cyg-apt got the wrong idea about the location of 
            # the tarfile after download?
            self.assert_(False)


    def testfind(self):
        # the find command equates with dpkg -S /path/to/file
        self.launchtest("./cyg-apt install " + self.package_name, self.v)[0]
        if tarfile.is_tarfile(self.expected_ballpath):
            input_tarfile = tarfile.open(self.expected_ballpath)
            contents = input_tarfile.getnames()
            found = False
            for f in contents:
                if os.path.isfile("/" + f):
                    found = True
                    break
            if not found:
                self.assert_(False)
            findout =\
                self.launchtest("./cyg-apt find " + "/" + f, self.v)[0]
            findout = findout.split()
            out_package_name = findout[0].split(":")[0]
            self.assert_(out_package_name == self.package_name)     
        else:
            self.assert_(False)

       
    def testbarred(self):
        # Test the safety mechanism which prevents the installation or 
        # removal of packages which cyg-apt itself depends on
        try:
            purgeout = self.launchtest("./cyg-apt purge " + self.package_name, self.v)[0]
            self.patch_cyg_apt_rc(self.cyg_apt_rc_file, "barred",\
                "testpkg", op="add")
            installout = self.launchtest("./cyg-apt install " +\
                self.package_name, self.v)[1]
            self.assert_("NOT installing" in installout)
            self.confirm_remove_clean(self.package_name)
            self.patch_cyg_apt_rc(self.cyg_apt_rc_file, None, None,\
                None, revert=True)
            installout = self.launchtest("./cyg-apt install " +\
                self.package_name, self.v)[0]
            self.confirm_installed(self.package_name)                
            self.patch_cyg_apt_rc(self.cyg_apt_rc_file, "barred",\
                "testpkg", op="add")
            removeout = self.launchtest("./cyg-apt remove " +\
                self.package_name, self.v)[1]
            self.assert_("NOT removing" in removeout)
            self.confirm_installed(self.package_name)
        finally:
            self.patch_cyg_apt_rc(self.cyg_apt_rc_file, None, None,\
                None, revert=True)
        
    
         
    def testlist(self):        
        regexes = {}
        regexes[0] = re.compile("([\w\-.]+)")
        regexes[1] = re.compile("([0-9a-z.-]+)")
        regexes[2] = re.compile("(\([\w.-]+\))")
        
        self.launchtest("./cyg-apt install " + self.package_name, self.v)[0]
        listout = self.launchtest("./cyg-apt list", self.v)[0]
        listout = listout.split("\n")
        listout = [x.strip() for x in listout if x.strip()   != ""]
        for l,index in zip(listout, range(len(listout))):
            if "--- Installed packages ---" in l:
                break
        self.assert_(index < len(listout) - 1)
        listout = listout[index + 1:]
        found_names = []
        found_vers = []
        for l in listout:
            items = l.split()
            self.assert_(2 <= len(items) <= 3)
            for i in range(len(items)):            
                match = regexes[i].search(items[i])
                if match:
                    found = match.groups()[0]
                    if (i == 0):
                        found_names.append(found)
                    elif (i == 1):
                        found_vers.append(found)
                else:
                    print "Problem cyg-apt list line :"
                    print l
                    self.assert_(False)
        self.assert_(self.package_name in found_names)
        self.assert_(self.ver in found_vers)
        
        
    def testmd5(self):
        self.launchtest("./cyg-apt install " + self.package_name, self.v)[0]
        md5out = self.launchtest\
            ("./cyg-apt md5 " + self.package_name, self.v)[0]
        md5out = md5out.splitlines()
        md5out = [x.split() for x in md5out]
        b = file(self.expected_ballpath,"rb").read()
        m = md5.new()
        m.update(b)
        digest = m.hexdigest()
        self.assert_(digest == md5out[0][0] == md5out[1][0])
        
    
    def testrequires(self):
        # package 2 is a dependency for package
        utilpack.popen_ext\
            ("./cyg-apt install " + self.package_name, self.v)[0]
        requiresout = utilpack.popen_ext\
            ("./cyg-apt requires " + self.package_name, self.v)[0].split()
        self.assert_(self.package_name_2 in requiresout)


    def testmissing(self):
        self.launchtest("./cyg-apt install " + self.package_name, self.v)[0]
        self.launchtest("./cyg-apt remove " + self.package_name_2, self.v)[0]
        missingout = self.launchtest\
            ("./cyg-apt missing " + self.package_name, self.v)[0].split()
        self.assert_(self.package_name_2 in missingout)
        
        
    def new_upgrade_test_setup(self, upgrade):
        utilpack.popen_ext("./cyg-apt install " + self.package_name, self.v)[0]
        setup_ini = self.opts["setup_ini"]
        setup_ini_basename_diff = os.path.basename(setup_ini) + ".diff"
        utilpack.popen_ext("/usr/bin/cp " + setup_ini + " " + setup_ini + ".save")
        cmd = "tools/setup_ini_diff_make.py "
        cmd += setup_ini + " "
        cmd += self.package_name + " "
        cmd += "install tarver --field-input "
        cmd += self.tarname + " 0.0.1-0 0.0.2-0"
        #setup_ini_diff_make.py setup-2.ini testpkg install tarver --field-input testpkg-0.0.1-0.tar.bz2 0.0.1-0 0.0.2-0
        utilpack.popen_ext(cmd)
        utilpack.popen_ext("patch " + setup_ini + " " + setup_ini_basename_diff)
        
        if (upgrade):
            cmd = "tools/setup_ini_diff_make.py "
            cmd += setup_ini + " "
            cmd += self.package_name + " "
            cmd += "install md5 --field-input "
            cmd += self.tarfile_2
            utilpack.popen_ext(cmd)
            utilpack.popen_ext("patch " + setup_ini + " " + setup_ini_basename_diff)

        
        
    def new_upgrade_test_cleanup(self):
        utilpack.popen_ext("./cyg-apt remove " + self.package_name)[0]
        setup_ini = self.opts["setup_ini"]
        setup_ini_basename_diff = os.path.basename(setup_ini) + ".diff"
        utilpack.popen_ext("/usr/bin/mv " + setup_ini + ".save" + " " + setup_ini)
        utilpack.popen_ext("/usr/bin/rm " + setup_ini_basename_diff)
        # It's a problem depending on cyg-apt to clean up after these tests
        #utilpack.popen("./cyg-apt remove " + self.package_name)
        
        
    def testversion(self):
        self.launchtest("./cyg-apt install " + self.package_name, self.v)[0]
        versionout = self.launchtest\
            ("./cyg-apt version " + self.package_name, self.v)[0]
        self.assert_(self.ver in versionout)
        

    def testnew(self):
        self.new_upgrade_test_setup(False)
        # -a flag overides always-update
        newout = self.launchtest("./cyg-apt -a new", self.v)[0]
        self.new_upgrade_test_cleanup()
        self.assert_(self.package_name in newout)
        
        
    def testupgrade(self):
        self.new_upgrade_test_setup(True)
        try:
            upgradeout = self.launchtest("./cyg-apt -a upgrade", self.v)[0]
            self.assert_fyes(self.version_2_marker)
        finally:
            self.new_upgrade_test_cleanup()
  
  
    def testcmdline_dist(self):
        self.launchtest("./cyg-apt purge " + self.package_name, self.v)[0]
        self.assert_fno(self.version_2_marker)
        installout = self.launchtest\
            ("./cyg-apt --dist=test install " + self.package_name, self.v)[0]
        try:
            self.assert_fyes(self.version_2_marker)
        finally:
            self.launchtest("./cyg-apt purge " + self.package_name, self.v)[0]
            
        
    def testcmdline_nodeps(self):
        self.launchtest("./cyg-apt remove " + self.package_name + " " +\
            self.package_name_2,self.v)[0]
        self.launchtest("./cyg-apt -x install " + self.package_name, self.v)[0]
        listout = self.launchtest("./cyg-apt list", self.v)[0]
        try:
            self.assert_(self.package_name in listout)
            self.assert_(self.package_name_2 not in listout)
            self.assert_fno(self.testpkg_lib_marker)
        finally:
            self.launchtest("./cyg-apt remove " + self.package_name, self.v)[0]
                

    def testcmdline_regexp(self):
        self.launchtest("./cyg-apt install " + self.package_name, self.v)[0]
        searchout = self.launchtest("./cyg-apt --regexp search "\
            + self.package_search_regex, self.v)[0]
        self.assert_("testpkg - is a test package" in searchout)
        self.assert_("testpkg-lib - supports test package" in searchout)
        findout = self.launchtest("./cyg-apt --regexp find "\
            + self.package_find_regex, self.v)[0]
        self.assert_("/usr/bin/testpkg.exe" in findout)
    
    
    def do_testupdate(self, command_line=""):
        setup_ini = self.opts["setup_ini"]
        setup_ini_basename_diff = os.path.basename(setup_ini) + ".diff"
        cmd = "tools/setup_ini_diff_make.py "
        cmd += self.opts["setup_ini"] + " "
        cmd += self.package_name + " "
        cmd += "install tarver --field-input "
        cmd += self.tarname + " 0.0.1-0 0.0.2-0"
        utilpack.popen_ext(cmd)
        utilpack.popen_ext("patch " + setup_ini + " " + setup_ini_basename_diff)
        update = self.launchtest("./cyg-apt " + command_line + " update", self.v)[0]
        diffout = utilpack.popen_ext\
        (\
            "diff " + self.opts["setup_ini"] + " " +\
            self.build_setup_ini
        )[0]
        self.assert_(diffout == "")    
    
    
    def testupdate(self):
        # DOS shell cyg-apt can't handle signatures
        if self.dostest:
            cmdline  = " -X "
        else:
            cmdline = ""
        try:
            self.do_testupdate(cmdline)
        finally:
            # Clean up in case failed test clobbered setup.ini
            self.launchtest("./cyg-apt update", self.v)


    def testshow(self):
        self.launchtest("./cyg-apt install " + self.package_name, self.v)[0]
        showout = self.launchtest\
            ("./cyg-apt show " + self.package_name, self.v)[0]
        self.assert_("testpkg - is a test package" in showout)
        
        
    def testsign(self):
        # Can't handle signatures under DOS shell
        if self.dostest:
            return
        # Make sure verification fails if underlying gpg verify cmd fails: 
        # remove the needed key
        delout = utilpack.popen_ext("gpg --batch --delete-secret-keys 9C7F3A392EF02971EFD2CAFBCE93017E7106F9ED")[0]
        delout = utilpack.popen_ext("gpg --batch --delete-keys 9C7F3A392EF02971EFD2CAFBCE93017E7106F9ED")[0]
        try:
            upout = self.launchtest("./cyg-apt update " +\
                self.package_name, self.v)[1]
            self.assert_("not signed by Cygwin's public key" in upout)
            # Make sure override works. Many other tests use the key normally.
            self.do_testupdate(command_line = "--no-verify ")
        finally:
            instout = self.launchtest("gpg --import cyg-apt-test-pub.gpg")
            instout = self.launchtest\
                ("gpg --allow-secret-key-import --import cyg-apt-test-sec.gpg")
        
        
    def testsource(self):
        self.launchtest("./cyg-apt source " + self.package_name, self.v)[0]
        # This may be confusing: the sourcemarker is a file in the  source 
        # package build that we need to know is there in the build before we 
        # can confidently expect it in the "installed" ie downloaded, unpacked # source package from the mini_mirror. It might be less confusing if I 
        # hadn't duplicated the files from the "binary" build.
        self.assert_fyes(self.sourcemarker)
        self.assert_fyes(self.sourcename)
        self.assert_fyes(self.source_unpack_marker)
        utilpack.popen_ext("/usr/bin/rm -rf " + self.sourcename)
    
    
    def testsearch(self):
        self.launchtest("./cyg-apt install " + self.package_name, self.v)[0]
        searchout = self.launchtest\
            ("./cyg-apt search " + self.package_name, self.v)[0]
        self.assert_("testpkg - is a test package" in searchout)
        
        
    def testurl(self):
        self.launchtest("./cyg-apt install " + self.package_name, self.v)
        urlout = utilpack.popen_ext\
            ("./cyg-apt url " + self.package_name, self.v)[0].strip()
        urlout = urlout.split("\n")
        urlout = urlout[-1]
        urlout = urlout.split("\r")
        urlout = urlout[-1]
        expect = self.opts["mirror"] + "/" + self.tarpath + self.tarname
        self.assert_(urlout == expect)
        
            
    def testpurge(self):
        self.launchtest("./cyg-apt install " + self.package_name, self.v)
        self.confirm_installed(self.package_name);        
        purgeout = self.launchtest("./cyg-apt purge " + self.package_name, self.v)[0]
        self.confirm_remove_clean(self.package_name)
        # Purge is a superset of remove clean cleanliness
        self.assert_fno(self.expected_ballpath)
        self.assert_fno(self.post_install_script_done)
        self.assert_fno(self.pre_remove_script_done)
        self.assert_fno(self.post_remove_script_done)
    

    def patch_cyg_apt_rc(self, cyg_apt_rc, option, new_val,\
        op, sep=" ", revert=False):
        if revert:
            if os.path.exists(self.cyg_apt_rc_file + ".testbak"):
                os.rename(self.cyg_apt_rc_file + ".testbak",\
                    self.cyg_apt_rc_file)
            return
        opts = {}
        rc_options = ['ROOT', 'mirror', 'cache', 'setup_ini', 'distname',\
            'barred']        
        rc = file(cyg_apt_rc).readlines()
        for i in rc:
            result = self.rc_regex.search(i)
            if result:
                k = result.group(1)
                v = result.group(2)
                if k in self.rc_options:
                    opts[k] = eval(v)            
            
            
        if op == "replace":
            opts[option] = new_val
        elif op == "add":
            opts[option] += sep + new_val
        else:
            self.assert_(False)
        h = open(self.cyg_apt_rc_file + ".testtmp", "w")
        for i in rc_options:
            h.write('%s="%s"\n' % (i, opts[i]))
        h.close()
        os.rename(self.cyg_apt_rc_file, self.cyg_apt_rc_file + ".testbak")
        os.rename(self.cyg_apt_rc_file + ".testtmp", self.cyg_apt_rc_file)

    
    def testpostinstall(self):
        self.launchtest\
            ("./cyg-apt remove " + self.package_name, self.v)
        self.confirm_remove_clean(self.package_name)
        # -y is an undocumented option to cyg-apt: suppresses postinstall
        self.launchtest\
            ("./cyg-apt -y install " + self.package_name, self.v)
        self.confirm_installed(self.package_name, nopostinstall=True)
        self.launchtest("./cyg-apt postinstall", self.v)
        self.confirm_installed(self.package_name, nopostinstall=False)

    
    def testpostremove(self):
        self.launchtest\
            ("./cyg-apt install " + self.package_name, self.v)
        self.confirm_installed(self.package_name)
        # -z is an undocumented option to cyg-apt: suppresses postremove
        self.launchtest\
            ("./cyg-apt -z remove " + self.package_name, self.v)
        self.confirm_remove_clean(self.package_name, nopostremove=True)
        self.launchtest("./cyg-apt postremove " + self.package_name, self.v)
        self.confirm_remove_clean(self.package_name, nopostremove=False)
    
    
    def testinstall_remove(self):
        self.launchtest\
            ("./cyg-apt remove " + self.package_name, self.v)
        self.confirm_remove_clean(self.package_name)
        self.launchtest\
            ("./cyg-apt install " + self.package_name, self.v)
        self.assert_(os.path.islink(self.symlink_location))
        # 3 == st_nlink, should be a named field: bugprone, easy to break
        # Test the hard link is actually a hard link -- note testpkg
        # will give the same result if hard link correctly formed
        self.assert_(os.stat(self.hard_link_location)[3] == 2)     
        self.confirm_installed(self.package_name)
        self.launchtest\
            ("./cyg-apt remove " + self.package_name, self.v)
        self.confirm_remove_clean(self.package_name)
        # At the end of this sequence we can expect scripts to reflect
        # the "freshly removed" state. Note we can't expect that after
        # the first remove since we don't know if the package was
        # ever present (or perhaps it was purged)
        self.assert_fyes(self.pre_remove_script_done)
        self.assert_fyes(self.post_remove_script_done)

   

    
    def launchtest(self, cmd, v=False):
        # This is a horrible hack but allows us to test DOS from Cygwin
        # in an automated way and with moderate confidence, without maintaining
        # a separate script.
        # The idea is to reset the child DOS shell back to a clean 
        # (non Cygwin) environment before running the test
        if not self.dostest:
            return utilpack.popen_ext(cmd, v)
        else:
            th_bat = file("test-harness.bat","w")
            th_bat.write("call reset.bat\n")
            th_bat.write("python " + cmd)
            th_bat.close()
            out = utilpack.popen_ext("cmd /c test-harness.bat", v)
            # Filter out the echo of our DOS environment reset batch file
            filt0 = out[0].split("\r\n")[2:]
            filt0 = string.join(filt0, "\n")
            filt1 = out[1].split("\r\n")
            filt1 = string.join(filt1, "\n")
            return filt0, filt1
        

    def testcmdline_mirror(self):
        if self.dostest:
            dosignore = "-X"
        else:
            dosignore = ""
        update_out = self.launchtest\
            ("./cyg-apt " + dosignore + " --mirror=bad update", self.v)[1]
        self.assert_("bad URL" in update_out)
        try:
            self.do_testupdate(command_line= dosignore + " --mirror=%s" % self.opts["mirror"])
        finally:
            # Clean up in case failed test clobbered setup.ini
            utilpack.popen_ext("./cyg-apt update", self.v)
        

    def testcmdline_download_only(self):
        purge_out = self.launchtest\
            ("./cyg-apt purge " + self.package_name, self.v)[1]
        install_out = self.launchtest\
            ("./cyg-apt --download install " + self.package_name, self.v)[1]
        self.confirm_remove_clean(self.package_name)
          
         
    def assert_fyes(self, f):
            self.assert_(os.path.exists(f) is True)
    
    
    def assert_fno(self, f):
            #print ">> " + f + " ===> " + str(os.path.exists(f)) + "!"
            self.assert_(os.path.exists(f) is False)    
    
    def tar_do(self, tarball, fn, notest=None):
        """ Applies fn to each file in a tarfile"""
        if tarfile.is_tarfile(tarball):
            input_tarfile = tarfile.open(tarball)
            contents = input_tarfile.getnames()
            contents = ["/" + f for f in contents]
            if notest:
                contents = [f for f in contents if f not in notest]
            for f in contents:
                if os.path.isfile(f):
                    fn(f)
        else:
            print sys.argv[0] + ": " + options.tarfile +\
            " is not a tarfile."
            self.assert_(0)

    
    def confirm_remove_clean(self, package, nopostremove=False):
        """ Confirms that no files or configuration file state exists for a package that has been subject to cyg-apt remove. """
        
        if nopostremove:
            notest = [self.pre_remove_script, self.post_remove_script]
        else:
            notest = None
        self.tar_do(self.tarfile, self.assert_fno, notest)
            
        # Next confirm that the filelist file is gone
        # Not the original cyg-apt behaviour but setup.exe removes
        # this file, so that's taken as correct behaviour.
        f = "/etc/setup/" + package + ".lst.gz"
        self.assert_(os.path.exists(f) is False)

        # Confirm the package is not represented in installed.db
        installed_db = file("/etc/setup/installed.db").readlines()
        for line in installed_db:
            self.assert_(line.split()[0] != package)

        if nopostremove:
            self.assert_fyes(self.pre_remove_marker)
            self.assert_fyes(self.post_remove_marker)
            self.assert_fyes(self.pre_remove_script)
            self.assert_fyes(self.post_remove_script)            
        else:
            self.assert_fno(self.pre_remove_marker)
            self.assert_fno(self.post_remove_marker)
            self.assert_fno(self.pre_remove_script)
            self.assert_fno(self.post_remove_script)
         
        

    def confirm_installed(self, package, nopostinstall=False):
        """ Confirms that a package is installed: the tarball files are 
        present, the package is represented in installed.db, if a postinstall script is present it's in the .done form, the filelist file exists and is correct."""
        
        self.tar_do(self.tarfile, self.assert_fyes)
        
        # Confirm that the postinstall script has run
        if not nopostinstall:
            self.assert_fyes(self.postinstall_marker)
        self.assert_fyes(self.post_remove_marker)
        
        # Confirm that the postinstall script has been moved
        # if postinstall performed, otherwise confirm ready to run
        if not nopostinstall:
            self.assert_fno(self.post_install_script)
            self.assert_fyes(self.post_install_script_done)
        else:
            self.assert_fyes(self.post_install_script)
            self.assert_fno(self.post_install_script_done)
        
if __name__ == '__main__':
    if "-d" in sys.argv:
        dostest = True
        sys.argv.remove("-d")
    else:
        dostest = False
    unittest.main(argv = sys.argv)
