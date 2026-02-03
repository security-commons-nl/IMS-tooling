---
description: How to deploy and run the IMS system
---

This workflow describes how to spin up the IMS backend and database using Docker.

1. Navigate to the project directory
2. Ensure Docker Desktop is running
3. Start the containers
// turbo
```bash
docker-compose up -d --build
```

4. Verify the containers are running
// turbo
```bash
docker ps
```

5. Check the API Documentation
   - Open Browser to: http://localhost:8000/docs
