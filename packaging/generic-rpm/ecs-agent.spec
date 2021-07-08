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

%global ecscni_goproject github.com/aws
%global ecscni_gorepo amazon-ecs-cni-plugins
%global ecscni_goimport %{ecscni_goproject}/%{ecscni_gorepo}
%global ecscni_gitrev 55b2ae77ee0bf22321b14f2d4ebbcc04f77322e1

%global vpccni_goproject github.com/aws
%global vpccni_gorepo amazon-vpc-cni-plugins
%global vpccni_goimport %{vpccni_goproject}/%{vpccni_gorepo}
%global vpccni_gitrev a21d3a41f922e14c19387713df66be3e4ee1e1f6
%global vpccni_gover 1.2

Name:           amazon-ecs-agent
Version:        1.53
Release:        1
License:        Apache 2.0
Summary:        Amazon Elastic Container Service initialization application
ExclusiveArch:  x86_64 aarch64

Source0:        sources.tgz
Source1:        ecs.service
Source2: https://%{ecscni_goimport}/archive/%{ecscni_gitrev}/%{ecscni_gorepo}.tar.gz
Source3: https://%{vpccni_goimport}/archive/%{vpccni_gitrev}/%{vpccni_gorepo}.tar.gz

BuildRequires:  systemd
Requires:       systemd
Requires:       iptables
Requires:       procps

%description
containerless agent.

%prep
%setup -c

%setup -T -D -a 2 -q

%setup -T -D -a 3 -q

# Symlink amazon-ecs-cni-plugins-%{ecscni_gitrev} to the GOPATH location
%cross_go_setup %{name}-%{version}/%{ecscni_gorepo}-%{ecscni_gitrev} %{ecscni_goproject} %{ecscni_goimport}
# Symlink amazon-vpc-cni-plugins-%{vpccni_gitrev} to the GOPATH location
%cross_go_setup %{name}-%{version}/%{vpccni_gorepo}-%{vpccni_gitrev} %{vpccni_goproject} %{vpccni_goimport}

%build
./scripts/build false %{gobuild_tag}

cd "${BUILD_TOP}"

# Build the ECS CNI plugins
# cross_go_configure cd's to the correct GOPATH location
%cross_go_configure %{ecscni_goimport}
LD_ECS_CNI_VERSION="-X github.com/aws/amazon-ecs-cni-plugins/pkg/version.Version=$(cat VERSION)"
ECS_CNI_HASH="%{ecscni_gitrev}"
LD_ECS_CNI_SHORT_HASH="-X github.com/aws/amazon-ecs-cni-plugins/pkg/version.GitShortHash=${ECS_CNI_HASH::8}"
LD_ECS_CNI_PORCELAIN="-X github.com/aws/amazon-ecs-cni-plugins/pkg/version.GitPorcelain=0"
go build -a \
  -buildmode=pie \
  -ldflags "-linkmode=external ${LD_ECS_CNI_VERSION} ${LD_ECS_CNI_SHORT_HASH} ${LD_ECS_CNI_PORCELAIN}" \
  -o ecs-eni \
  ./plugins/eni
go build -a \
  -buildmode=pie \
  -ldflags "-linkmode=external ${LD_ECS_CNI_VERSION} ${LD_ECS_CNI_SHORT_HASH} ${LD_ECS_CNI_PORCELAIN}" \
  -o ecs-ipam \
  ./plugins/ipam
go build -a \
  -buildmode=pie \
  -ldflags "-linkmode=external ${LD_ECS_CNI_VERSION} ${LD_ECS_CNI_SHORT_HASH} ${LD_ECS_CNI_PORCELAIN}" \
  -o ecs-bridge \
  ./plugins/ecs-bridge

cd "${BUILD_TOP}"

# Build the VPC CNI plugins
# cross_go_configure cd's to the correct GOPATH location
%cross_go_configure %{vpccni_goimport}
LD_VPC_CNI_VERSION="-X github.com/aws/amazon-vpc-cni-plugins/version.Version=%{vpccni_gover}"
VPC_CNI_HASH="%{vpccni_gitrev}"
LD_VPC_CNI_SHORT_HASH="-X github.com/aws/amazon-vpc-cni-plugins/version.GitShortHash=${VPC_CNI_HASH::8}"
go build -a \
  -buildmode=pie \
  -ldflags "-linkmode=external ${LD_VPC_CNI_VERSION} ${LD_VPC_CNI_SHORT_HASH} ${LD_VPC_CNI_PORCELAIN}" \
  -mod=vendor \
  -o vpc-branch-eni \
  ./plugins/vpc-branch-eni

%install
install -D generic_rpm %{buildroot}%{_libexecdir}/amazon-ecs-agent
install -D %{_topdir}/packaging/generic-rpm/ipSetup.sh %{buildroot}%{_libexecdir}/ipSetup.sh
install -D %{_topdir}/packaging/generic-rpm/ipCleanup.sh %{buildroot}%{_libexecdir}/ipCleanup.sh
install -D -p -m 0755 %{ecscni_gorepo}-%{ecscni_gitrev}/ecs-bridge %{buildroot}%{libexecdir}/amazon-ecs-agent/ecs-bridge
install -D -p -m 0755 %{ecscni_gorepo}-%{ecscni_gitrev}/ecs-eni %{buildroot}%{libexecdir}/amazon-ecs-agent/ecs-eni
install -D -p -m 0755 %{ecscni_gorepo}-%{ecscni_gitrev}/ecs-ipam %{buildroot}%{libexecdir}/amazon-ecs-agent/ecs-ipam
install -D -p -m 0755 %{vpccni_gorepo}-%{vpccni_gitrev}/vpc-branch-eni %{buildroot}%{libexecdir}/amazon-ecs-agent/vpc-branch-eni

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

