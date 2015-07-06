%global _hardened_build 1
%global  fastnetmon_attackdir   %{_localstatedir}/log/fastnetmon_attacks
%global  fastnetmon_user        root
%global  fastnetmon_group       %{fastnetmon_user}
%global  fastnetmon_config_path %{_sysconfdir}/fastnetmon.conf

Name:       fastnetmon
Version:    1.1.2
Release:    1%{?dist}

Summary:    A very fast DDoS analyzer with sflow/netflow/mirror support       
Group:      System Environment/Daemons
License:    GPLv2
URL:        https://github.com/FastVPSEestiOu/fastnetmon

Source0:    https://github.com/FastVPSEestiOu/fastnetmon/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:     git, make, gcc, gcc-c++, boost-devel, GeoIP-devel, log4cpp-devel
BuildRequires:     ncurses-devel, boost-thread, boost-regex, libpcap-devel, gpm-devel, clang, cmake
BuildRequires:     systemd

Requires:          log4cpp, libpcap, boost-thread, boost-thread, boost-regex
Requires(pre):     shadow-utils
Requires(post):    systemd
Requires(preun):   systemd
Requires(postun):  systemd

Provides:          fastnetmon

%description
A high performance DoS/DDoS load analyzer built on top of multiple packet capture
engines (NetFlow, IPFIX, sFLOW, netmap, PF_RING, PCAP).

%prep
%autosetup

%build
cd src
mkdir build
cd build
# We should disable PF_RING plugon support because we did not have it in repository 
cmake .. -DDISABLE_PF_RING_SUPPORT=ON
make

%install
# modify systemd file for Fedora compliance
sed 's/\/opt\/fastnetmon\/fastnetmon/\/usr\/sbin\/fastnetmon/' src/fastnetmon.service > src/fastnetmon.service.patched
# install init script
install -p -D -m 0755 src/fastnetmon.service.patched %{buildroot}%{_sysconfdir}/systemd/system/fastnetmon.service

# install daemon binary file
install -p -D -m 0755 src/build/fastnetmon %{buildroot}%{_sbindir}/fastnetmon

# install client binary file 
install -p -D -m 0755 src/build/fastnetmon_client %{buildroot}%{_bindir}/fastnetmon_client

# install config
install -p -D -m 0755 src/fastnetmon.conf %{buildroot}%{fastnetmon_config_path}

# Create log folder
install -p -d -m 0700 %{buildroot}%{fastnetmon_attackdir}

%pre

%post
%systemd_post fastnetmon.service

if [ $1 -eq 2 ]; then
    # upgrade
    chmod 700 %{fastnetmon_attackdir}
fi

%preun
%systemd_preun fastnetmon.service

%postun
%systemd_postun_with_restart fastnetmon.service 

%files
#%doc LICENSE CHANGES README
# init script
%{_sysconfdir}/systemd/system

# binary daemon
%{_sbindir}/fastnetmon
%{_bindir}/fastnetmon_client

%config(noreplace) %{_sysconfdir}/fastnetmon.conf
%attr(700,%{fastnetmon_user},%{fastnetmon_group}) %dir %{fastnetmon_attackdir}


%changelog
* Thu Jun 04 2015 Arun Babu Neelicattu <arun.neelicattu@gmail.com> - 1.1.1-1
- Update upstream specfile for initial release

* Mon Mar 23 2015 Pavel Odintsov <pavel.odintsov@gmail.com> - 1.1.1-1
- First RPM package release
