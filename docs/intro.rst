Introduction
-------------

CaaStle is a command-line tool for creating cloud environments for containerized applications.

An environment for a cloud native containerized application consists of

- Container Orchestration Engine (COE) cluster (e.g Amazon ECS, Kubernetes) and

- Managed cloud services (e.g. Amazon RDS, Google Cloud SQL) and

Application containers are deployed on such a cloud environment.

Currently such environments are not easy to create, share, and reproduce because managed cloud services are not integral part of the application architecture definition.

CaaStle solves this problem by providing a ‘Platform-as-Code’ solution that supports creating cloud environments 
using a declarative approach and supporting application deployments on such environments.





