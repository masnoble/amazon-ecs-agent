# Copyright 2014-2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the
# "License"). You may not use this file except in compliance
# with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and
# limitations under the License.

%global gobuild_tag generic_rpm
%global _cachedir %{_localstatedir}/cache
%global bundled_agent_version %{version}
%global no_exec_perm 644


Name:           amazon-ecs-agent
Version:        1.53
Release:        1
License:        Apache 2.0
Summary:        Amazon Elastic Container Service initialization application
ExclusiveArch:  x86_64 aarch64

Source0:        sources.tgz
Source1:        ecs.service

BuildRequires:  systemd
Requires:       systemd
Requires:       iptables
Requires:       procps

%description
containerless agent.

%prep
%setup -c

%build
./scripts/build false %{gobuild_tag}

%install
install -D generic_rpm %{buildroot}%{_libexecdir}/amazon-ecs-agent
install -D %{_topdir}/packaging/generic-rpm/ipSetup.sh %{buildroot}%{_libexecdir}/ipSetup.sh
install -D %{_topdir}/packaging/generic-rpm/ipCleanup.sh %{buildroot}%{_libexecdir}/ipCleanup.sh

mkdir -p %{buildroot}%{_sysconfdir}/ecs
touch %{buildroot}%{_sysconfdir}/ecs/ecs.config
touch %{buildroot}%{_sysconfdir}/ecs/ecs.config.json


mkdir -p %{buildroot}%{_sharedstatedir}/ecs/data

install -m %{no_exec_perm} -D %{SOURCE1} $RPM_BUILD_ROOT/%{_unitdir}/ecs.service

%files
%{_libexecdir}/amazon-ecs-agent
%{_libexecdir}/ipSetup.sh
%{_libexecdir}/ipCleanup.sh
%config(noreplace) %ghost %{_sysconfdir}/ecs/ecs.config
%config(noreplace) %ghost %{_sysconfdir}/ecs/ecs.config.json
%dir %{_sharedstatedir}/ecs/data
%{_unitdir}/ecs.service

%post
%systemd_post ecs

%postun
%systemd_postun

