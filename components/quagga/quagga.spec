%define with_pimd   0
%define with_fpm    1

%define quagga_uid  92
%define quagga_gid  92
%define vty_group   quaggavt
%define vty_gid     85

%global _hardened_build 1

Name: quagga
Version: 0.99.24.1
Release: 4%{?dist}
Summary: Routing daemon
License: GPLv2+
Group: System Environment/Daemons
URL: http://www.quagga.net
Source0: http://download.savannah.gnu.org/releases/quagga/%{name}-%{version}.tar.xz
Source1: quagga-filter-perl-requires.sh
Source2: quagga-tmpfs.conf
%if %with_pimd
Source3: quagga-pimd-service-and-init.patch
%endif
BuildRequires: systemd
BuildRequires: net-snmp-devel
BuildRequires: texinfo libcap-devel texi2html
BuildRequires: readline readline-devel ncurses ncurses-devel
Requires: net-snmp ncurses
Requires(post): systemd /sbin/install-info
Requires(preun): systemd /sbin/install-info
Requires(postun): systemd
Provides: routingdaemon = %{version}-%{release}
Obsoletes: quagga-sysvinit

Patch0: 0001-systemd-change-the-WantedBy-target.patch
Patch1: 0001-zebra-raise-the-privileges-before-calling-socket.patch
%if %with_pimd
Patch2: quagga-pimd-service-and-init.patch
%endif

%define __perl_requires %{SOURCE1}

%description
Quagga is free software that operates TCP/IP-based routing protocols. It takes
a multi-server and multi-threaded approach to resolving the current complexity
of the Internet.

Quagga supports BGP4, BGP4+, BGP4-, IS-IS (experimental), OSPFv2,
OSPFv3, PIM RIPv1, RIPv2, and RIPng.

Quagga is intended to be used as a Route Server and a Route Reflector. It is
not a toolkit; it provides full routing power under a new architecture.
Quagga by design has a process for each protocol.

Quagga is a fork of GNU Zebra.

%package contrib
Summary: Contrib tools for quagga
Group: System Environment/Daemons

%description contrib
Contributed/3rd party tools which may be of use with quagga.

%package devel
Summary: Header and object files for quagga development
Group: System Environment/Daemons
Requires: %{name} = %{version}-%{release}

%description devel
The quagga-devel package contains the header and object files necessary for
developing OSPF-API and quagga applications.

%prep
%setup -q

%patch0 -p1
%patch1 -p1
%if %with_pimd
%patch2 -p1
%endif

%build
%configure \
    --sysconfdir=%{_sysconfdir}/quagga \
    --libdir=%{_libdir}/quagga \
    --libexecdir=%{_libexecdir}/quagga \
    --localstatedir=%{_localstatedir}/run/quagga \
    --enable-ipv6=yes \
    --enable-isisd=yes \
%if %with_pimd
    --enable-pimd=yes \
%endif
    --enable-snmp=agentx \
    --enable-multipath=64 \
    --enable-opaque-lsa \
    --enable-ospf-te \
    --enable-vtysh=yes \
    --enable-ospfclient=no \
    --enable-ospfapi=no \
    --enable-user=quagga \
    --enable-group=quagga \
    --enable-vty-group=%vty_group \
    --enable-rtadv \
    --disable-exampledir \
    --enable-netlink \
%if %with_fpm
    --enable-tcp-zebra \
    --enable-fpm \
%endif
    --enable-gcc-rdynamic \
    --with-pkg-extra-version=-CloudRouter-Edition

make %{?_smp_mflags} MAKEINFO="makeinfo --no-split" CFLAGS="%{optflags} -fno-strict-aliasing"

pushd doc
texi2html quagga.texi
popd

%install
mkdir -p %{buildroot}/etc/{quagga,rc.d/init.d,sysconfig,logrotate.d} \
         %{buildroot}/var/log/quagga %{buildroot}%{_infodir} \
         %{buildroot}%{_unitdir}

make DESTDIR=%{buildroot} INSTALL="install -p" CP="cp -p" install

# Remove this file, as it is uninstalled and causes errors when building on RH9
rm -rf %{buildroot}/usr/share/info/dir

install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/zebra.service %{buildroot}%{_unitdir}/zebra.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/isisd.service %{buildroot}%{_unitdir}/isisd.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/ripd.service %{buildroot}%{_unitdir}/ripd.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/ospfd.service %{buildroot}%{_unitdir}/ospfd.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/bgpd.service %{buildroot}%{_unitdir}/bgpd.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/ospf6d.service %{buildroot}%{_unitdir}/ospf6d.service
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/ripngd.service %{buildroot}%{_unitdir}/ripngd.service
%if %with_pimd
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/pimd.service %{buildroot}%{_unitdir}/pimd.service
%endif

install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/quagga.sysconfig %{buildroot}/etc/sysconfig/quagga
install -p -m 644 %{_builddir}/%{name}-%{version}/redhat/quagga.logrotate %{buildroot}/etc/logrotate.d/quagga

install -d -m 770  %{buildroot}/var/run/quagga

install -d -m 755 %{buildroot}/%{_tmpfilesdir}
install -p -m 644 %{SOURCE2} %{buildroot}/%{_tmpfilesdir}/quagga.conf

rm %{buildroot}%{_libdir}/quagga/*.a
rm %{buildroot}%{_libdir}/quagga/*.la

%pre
getent group %vty_group >/dev/null 2>&1 || groupadd -r -g %vty_gid %vty_group >/dev/null 2>&1 || :
getent group quagga >/dev/null 2>&1 || groupadd -g %quagga_gid quagga >/dev/null 2>&1 || :
getent passwd quagga >/dev/null 2>&1 || useradd -u %quagga_uid -g %quagga_gid -M -r -s /sbin/nologin \
 -c "Quagga routing suite" -d %{_localstatedir}/run/quagga quagga >/dev/null 2>&1 || :

%post
%systemd_post zebra.service
%systemd_post isisd.service
%systemd_post ripd.service
%systemd_post ospfd.service
%systemd_post bgpd.service
%systemd_post ospf6d.service
%systemd_post ripngd.service
%if %with_pimd
%systemd_post pimd.service
%endif

if [ -f %{_infodir}/%{name}.inf* ]; then
    install-info %{_infodir}/quagga.info %{_infodir}/dir || :
fi

# Create dummy files if they don't exist so basic functions can be used.
if [ ! -e %{_sysconfdir}/quagga/zebra.conf ]; then
    echo "hostname `hostname`" > %{_sysconfdir}/quagga/zebra.conf
    chown quagga:quagga %{_sysconfdir}/quagga/zebra.conf
    chmod 640 %{_sysconfdir}/quagga/zebra.conf
fi
if [ ! -e %{_sysconfdir}/quagga/vtysh.conf ]; then
    touch %{_sysconfdir}/quagga/vtysh.conf
    chmod 640 %{_sysconfdir}/quagga/vtysh.conf
    chown quagga:%{vty_group} %{_sysconfdir}/quagga/vtysh.conf
fi
if [ ! -e %{_sysconfdir}/quagga/bgpd.conf ]; then
    touch %{_sysconfdir}/quagga/bgpd.conf
    chmod 640 %{_sysconfdir}/quagga/bgpd.conf
    chown quagga:quagga %{_sysconfdir}/quagga/bgpd.conf
fi
if [ ! -e %{_sysconfdir}/quagga/ospfd.conf ]; then
    touch %{_sysconfdir}/quagga/ospfd.conf
    chmod 640 %{_sysconfdir}/quagga/ospfd.conf
    chown quagga:quagga %{_sysconfdir}/quagga/ospfd.conf
fi
if [ ! -e %{_sysconfdir}/quagga/ospf6d.conf ]; then
    touch %{_sysconfdir}/quagga/ospf6d.conf
    chmod 640 %{_sysconfdir}/quagga/ospf6d.conf
    chown quagga:quagga %{_sysconfdir}/quagga/ospf6d.conf
fi
if [ ! -e %{_sysconfdir}/quagga/isisd.conf ]; then
    touch %{_sysconfdir}/quagga/isisd.conf
    chmod 640 %{_sysconfdir}/quagga/isisd.conf
    chown quagga:quagga %{_sysconfdir}/quagga/isisd.conf
fi
if [ ! -e %{_sysconfdir}/quagga/ripd.conf ]; then
    touch %{_sysconfdir}/quagga/ripd.conf
    chmod 640 %{_sysconfdir}/quagga/ripd.conf
    chown quagga:quagga %{_sysconfdir}/quagga/ripd.conf
fi
if [ ! -e %{_sysconfdir}/quagga/ripngd.conf ]; then
    touch %{_sysconfdir}/quagga/ripngd.conf
    chmod 640 %{_sysconfdir}/quagga/ripngd.conf
    chown quagga:quagga %{_sysconfdir}/quagga/ripngd.conf
fi
%if %with_pimd
if [ ! -e %{_sysconfdir}/quagga/pimd.conf ]; then
    touch %{_sysconfdir}/quagga/pimd.conf
    chmod 640 %{_sysconfdir}/quagga/pimd.conf
    chown quagga:quagga %{_sysconfdir}/quagga/pimd.conf
fi
%endif

%postun
%systemd_postun_with_restart zebra.service
%systemd_postun_with_restart isisd.service
%systemd_postun_with_restart ripd.service
%systemd_postun_with_restart ospfd.service
%systemd_postun_with_restart bgpd.service
%systemd_postun_with_restart ospf6d.service
%systemd_postun_with_restart ripngd.service
%if %with_pimd
%systemd_postun_with_restart pimd.service
%endif

if [ -f %{_infodir}/%{name}.inf* ]; then
    install-info --delete %{_infodir}/quagga.info %{_infodir}/dir || :
fi

%preun
%systemd_preun zebra.service
%systemd_preun isisd.service
%systemd_preun ripd.service
%systemd_preun ospfd.service
%systemd_preun bgpd.service
%systemd_preun ospf6d.service
%systemd_preun ripngd.service
%if %with_pimd
%systemd_preun pimd.service
%endif

%files
%defattr(-,root,root)
%doc AUTHORS COPYING
%doc zebra/zebra.conf.sample
%doc isisd/isisd.conf.sample
%doc ripd/ripd.conf.sample
%doc bgpd/bgpd.conf.sample*
%doc ospfd/ospfd.conf.sample
%doc ospf6d/ospf6d.conf.sample
%doc ripngd/ripngd.conf.sample
%doc doc/quagga.html
%doc doc/mpls
%doc ChangeLog INSTALL NEWS README REPORTING-BUGS SERVICES TODO
%dir %attr(750,quagga,quagga) %{_sysconfdir}/quagga
%dir %attr(750,quagga,quagga) /var/log/quagga
%dir %attr(750,quagga,quagga) /var/run/quagga
%{_infodir}/*info*
%{_mandir}/man*/*
%exclude %{_mandir}/man*/watchquagga.*
%{_sbindir}/*
%exclude %{_sbindir}/watchquagga
%{_bindir}/*
%dir %{_libdir}/quagga
%{_libdir}/quagga/*.so.*
%config(noreplace) %attr(640,root,root) /etc/logrotate.d/quagga
%config(noreplace) /etc/sysconfig/quagga
%{_tmpfilesdir}/quagga.conf
%{_unitdir}/*.service

%files contrib
%defattr(-,root,root)
%doc AUTHORS COPYING %attr(0644,root,root) tools

%files devel
%defattr(-,root,root)
%doc AUTHORS COPYING
%dir %{_libdir}/quagga/
%{_libdir}/quagga/*.so
%dir %{_includedir}/quagga
%{_includedir}/quagga/*.h
%dir %{_includedir}/quagga/ospfd
%{_includedir}/quagga/ospfd/*.h

%changelog
* Sat Jun 11 2015 Martin Winter <mwinter@opensourcerouting.org> 0.99.24.1-4
- Added conditional PIMd (disabled by default as it's experimental) to SPEC
- Added conditional FPM interface (enabled by default) to SPEC
- Removed Babel (Was removed just after 0.99.24.1 from Quagga Distribution
  for licensing issues)
- Marked Quagga Version as CloudRouter edition
- forced enable-gcc-rdynamic to make sure to improve chances for
  tracebacks in crashes

* Mon May 4 2015 Jay Turner <jturner@iix.net> - 0.99.24.1
- Initial build
