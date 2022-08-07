# Overview

Python script used for deploying Azure Logic Apps

Can deploy single or multiple templates in dirs (recursively)

## Usage

```
python main.py
    -p                  {path_to_dir_or_file}
    -rg                 {resource_group_name}
    --subscription      {subscription_id}
    --tenant            {tenant_id}
    --client_id         {client_id}
    --client_secret     {client_secret}
```

---

Run & Connect to container:

```
docker-compose up -d --build && docker exec -it deploy-logic_apps sh
```
