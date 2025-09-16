# Deployment

Deploying to the server is done via Ansible script which is a separate package, found [here](github.com/ecolistening/echodash-server-ansible/).

```
git clone git@github.com:ecolistening/echodash-server-ansible.git
cd echodash-server-ansible
```

Adjust the `echodash-server-ansible/vars/common.yml` to suit your needs (staging or production):

```
repo_link: 'git@github.com:ecolistening/ecoacoustics-dashboard.git'
user_name: {staging|production}
domain_name: echodash.co.uk
data_location: /path/to/{staging|production}/data
commit: {staging|production|commitref}
env_file: .env.{staging|production}
```

Adjust `echodash-server-ansible/inventory`

```
[echodash]
{IP_ADDR} ansible_user={staging|production}
```

Run the deployment script
```
uv run ansible-playbook -i inventory install-the-dashboard.yml -K
```

## Setting up a new server

When provisioning a new server, we host two different linux users, a 'production' environment for public facing use, and a 'staging' environment for testing deployments before pushing to production. These need to be setup before deployment.

```
# create the user and home directory (-m flag)
sudo useradd -m {staging|production}
# add to sudo'ers
sudo usermod -a -G sudo {staging|production}
sudo passwd {staging|production}
ssh-copy-id -i ~/.ssh/id_ed25519.pub {staging|production}@{IPADDR}
```

Now follow the remainder of the instructions on [echodash-server-ansible](github.com/ecolistening/echodash-server-ansible/).
