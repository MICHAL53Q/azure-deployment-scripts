# Overview

Python script used for deploying Azure Function Apps

## Usage

```
python main.py
    -p                  {path_to_zip_file}
    -rg                 {resource_group_name}
    -n                  {function_app_name}
    --subscription      {subscription_id}
    --tenant            {tenant_id}
    --client_id         {client_id}
    --client_secret     {client_secret}
```

---

Run & Connect to container:

```
docker-compose up -d --build && docker exec -it deploy-function_apps sh
```
