Use setup/ teardown to run data quality checks before running a rose classification model
=========================================================================================

This repository contains the DAG code used in the [Use setup/ teardown to run data quality checks before running a rose classification model](https://docs.astronomer.io/learn/use-case-setup-teardown-data-quality). 

The DAGs in this repository use the following packages:

- [Postgres Airflow Provider](https://registry.astronomer.io/providers/apache-airflow-providers-postgres/versions/latest)
- [Common SQL Airflow Provider](https://registry.astronomer.io/providers/apache-airflow-providers-common-sql/versions/latest)
- [Astro Python SDK](https://registry.astronomer.io/providers/astro-sdk-python/versions/latest)
- [Scikit-learn](https://scikit-learn.org/stable/)
- [Matplotlib](https://matplotlib.org/)
- [Seaborn](https://seaborn.pydata.org/)

# How to use this repository

This section explains how to run this repository with Airflow. Note that you will need to copy the contents of the `.env_example` file to a newly created `.env` file. No external connections are necessary to run this repository locally, but you can add your own credentials in the file if you wish to connect to your tools. 

## Option 1: Use GitHub codespaces

Run this Airflow project without installing anything locally.

1. Fork this repository.
2. Create a new GitHub codespaces project on your fork. Make sure it uses at least 4 cores!
3. After creating the codespaces project the Astro CLI will automatically start up all necessary Airflow components and the local MinIO and MLflow instances. This can take a few minutes. 
4. Once the Airflow project has started, access the Airflow UI by clicking on the **Ports** tab and opening the forward URL for port 8080.

## Option 2: Use the Astro CLI

Download the [Astro CLI](https://docs.astronomer.io/astro/cli/install-cli) to run Airflow locally in Docker. `astro` is the only package you will need to install locally.

1. Run `git clone https://github.com/astronomer/use-case-setup-teardown-data-quality.git` on your computer to create a local clone of this repository.
2. Install the Astro CLI by following the steps in the [Astro CLI documentation](https://docs.astronomer.io/astro/cli/install-cli). Docker Desktop/Docker Engine is a prerequisite, but you don't need in-depth Docker knowledge to run Airflow with the Astro CLI.
3. Run `astro dev start` in your cloned repository.
4. After your Astro project has started. View the Airflow UI at `localhost:8080`.

## Resources

- [Use setup/ teardown to run data quality checks before running a rose classification model](https://docs.astronomer.io/learn/use-case-setup-teardown-data-quality).
- [Use setup and teardown tasks in Airflow](https://docs.astronomer.io/learn/airflow-setup-teardown)
- [Run data quality checks using SQL check operators](https://docs.astronomer.io/learn/airflow-sql-data-quality).
- [Datasets and data-aware scheduling in Airflow](https://docs.astronomer.io/learn/airflow-datasets).
- [Astro Python SDK tutorial](https://docs.astronomer.io/learn/astro-python-sdk).
- [Astro Python SDK documentation](https://astro-sdk-python.readthedocs.io/en/stable/index.html).
- [Astro Python SDK repository](https://github.com/astronomer/astro-sdk).