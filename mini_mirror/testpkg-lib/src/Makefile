BUILDDIR =  ../build
TARFILE = testpkg-lib-0.0.1-1.tar.bz2
TOOLS = ../../../tools/
TESTPKG-LIB-MARKER = testpkg-lib.marker
all:
	# Create the tarball
	touch ../build/root/usr/lib/$(TESTPKG-LIB-MARKER)
	cd $(BUILDDIR)/root ; pwd ; tar --exclude=".svn" -jcf $(TARFILE) *;\
mv $(TARFILE) ../release-2/testpkg-lib;\

	# Copy the default .ini to the build directory
	/usr/bin/cp ../../setup-2.ini ../build

	/usr/bin/cp setup.hint $(BUILDDIR)/release-2/testpkg-lib
	$(TOOLS)md5.sum.py -f ../build/release-2/testpkg-lib/ ../build/release-2/testpkg-lib/md5.sum
ifdef CYGAPT_TESTMIRROR
	scp ../build/release-2/testpkg-lib/* $(CYGAPT_TESTMIRROR)/release-2/testpkg-lib
endif # CYGAPT_TESTMIRROR
	$(TOOLS)setup_ini_diff_make.py ../../setup-2.ini testpkg-lib install md5 --field-input=../build/release-2/testpkg-lib/testpkg-lib-0.0.1-1.tar.bz2
	patch ../../setup-2.ini setup-2.ini.diff

	/usr/bin/rm -f ../../setup-2.ini.sig 
	gpg -u "cyg-apt"  --output ../../setup-2.ini.sig --detach-sig ../../setup-2.ini
	bzip2 -k -c ../../setup-2.ini > ../../setup-2.bz2
ifdef CYGAPT_TESTMIRROR
	scp ../../setup-2.ini ../../setup-2.ini.sig ../../setup-2.bz2 $(CYGAPT_TESTMIRROR)
endif # CYGAPT_TESTMIRROR
	/usr/bin/rm -rf setup-2.ini.diff	

clean:
	rm ../build/root/usr/lib/$(TESTPKG-LIB-MARKER)
	/usr/bin/rm -f ../build/release-2/testpkg-lib/*
	$(TOOLS)hasfiles.py ../build svn
	/usr/bin/rm -f setup-2.ini
