# Deployment

Deploying to the server is done via Ansible script which is a separate package, found [here](github.com/ecolistening/echodash-server-ansible/).

```
git clone git@github.com:ecolistening/echodash-server-ansible.git
```

When provisioning a new server, these Ansible scripts require:

1) A 'production' user is setup
2) A 'staging' user is setup

## Setting up a server for deployment

## Production
```
sudo useradd -m production
sudo usermod -a -G sudo production
ssh-copy-id -i ~/.ssh/id_ed25519.pub production@{IPADDR}
```

Adjust the `echodash-server-ansible/vars/common.yml`:

```
repo_link: 'git@github.com:ecolistening/ecoacoustics-dashboard.git'
user_name: production
domain_name: echodash.co.uk
data_location: /path/to/production/data
commit: main
env_file: .env.production
```

## Staging
```
sudo useradd -m staging
sudo usermod -a -G sudo staging
ssh-copy-id -i ~/.ssh/id_ed25519.pub staging@{IPADDR}
```

Adjust the `echodash-server-ansible/vars/common.yml`:

```
repo_link: 'git@github.com:ecolistening/ecoacoustics-dashboard.git'
user_name: staging
domain_name: echodash.co.uk
data_location: /path/to/staging/data
commit: staging # or any other commit you want to try out in the staging environment
env_file: .env.staging
```

Follow the remaining deployment instructions in echodash.
