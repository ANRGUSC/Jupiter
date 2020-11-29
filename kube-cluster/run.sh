ansible-playbook -i hosts init.yml
ansible-playbook -i hosts dependencies.yml
ansible-playbook -i hosts master.yml
ansible-playbook -i hosts workers.yml
