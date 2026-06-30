# Deploy Checklist

> Ver [`DEPLOYMENT.md`](../../DEPLOYMENT.md) para la guía completa de deploy.
> Ver [`dashboard/start.sh`](../../dashboard/start.sh) para el script de deploy.
>
> Checklist resumido:
> 1. `git pull --ff-only`
> 2. `bash dashboard/start.sh`
> 3. Verificar: `curl -k https://10.0.0.227/api/health`
> 4. Verificar: `sudo systemctl status agentic-software-boutique`