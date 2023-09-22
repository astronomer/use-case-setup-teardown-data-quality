"""
## Use setup/ teardown with data quality checks during creation of a Postgres table

This DAG demonstrates a table creation pattern which includes both halting and 
non-halting data quality checks. Setup/ teardown tasks are used to create and
drop temporary tables.

To use this DAG you will need to provide the `postgres_default` connection.
"""

from airflow import Dataset
from airflow.decorators import dag, task, task_group
from airflow.models.baseoperator import chain
from pendulum import datetime
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.common.sql.operators.sql import (
    SQLColumnCheckOperator,
    SQLTableCheckOperator,
)

POSTGRES_CONN_ID = "postgres_default"
TABLE_NAME = "roses"
SCHEMA_NAME = "public"
CSV_PATH = "/include/roses_raw.csv"


@dag(
    start_date=datetime(2023, 8, 1),
    schedule="@daily",
    catchup=False,
    tags=["setup/teardown", "data quality"],
    default_args={"postgres_conn_id": POSTGRES_CONN_ID, "conn_id": POSTGRES_CONN_ID},
)
def create_rose_table():
    @task_group
    def create_table():
        create_tmp = PostgresOperator(
            task_id="create_tmp",
            sql=f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}_tmp (
                    index int,
                    petal_size_cm float,
                    stem_length_cm float,
                    leaf_size_cm float,
                    blooming_month varchar(50),
                    rose_type varchar(50)
                );""",
        )

        load_data_into_tmp = PostgresOperator(
            task_id="load_data_into_tmp",
            sql=f"""
                    BEGIN;
                    CREATE TEMP TABLE copy_tmp_table 
                    (LIKE {TABLE_NAME}_tmp INCLUDING DEFAULTS)
                    ON COMMIT DROP;
                        
                    COPY copy_tmp_table FROM '{CSV_PATH}' 
                    DELIMITER ',' CSV HEADER;
                        
                    INSERT INTO {TABLE_NAME}_tmp
                    SELECT *
                    FROM copy_tmp_table
                    ON CONFLICT DO NOTHING;
                    COMMIT;
                """,
        )

        @task_group
        def test_tmp():
            SQLColumnCheckOperator(
                task_id="test_cols",
                retry_on_failure="True",
                table=f"{SCHEMA_NAME}.{TABLE_NAME}_tmp",
                column_mapping={
                    "petal_size_cm": {"min": {"geq_to": 5}, "max": {"leq_to": 11}},
                    "stem_length_cm": {"min": {"geq_to": 19}, "max": {"leq_to": 51}},
                    "leaf_size_cm": {"min": {"geq_to": 3}, "max": {"leq_to": 9}},
                },
                accept_none="True",
            )

            SQLTableCheckOperator(
                task_id="test_table",
                retry_on_failure="True",
                table=f"{SCHEMA_NAME}.{TABLE_NAME}_tmp",
                checks={
                    "row_count_check": {"check_statement": "COUNT(*) > 500"},
                    "rose_type_check": {
                        "check_statement": "rose_type IN ('damask', 'tea', 'moss')"
                    },
                },
            )

        swap = PostgresOperator(
            task_id="swap",
            sql=f"""
                DO
                $$
                BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = '{TABLE_NAME}' AND table_schema = 'public'
                ) 
                THEN
                    EXECUTE 'ALTER TABLE ' || '{TABLE_NAME}' || ' RENAME TO ' || '{TABLE_NAME}_backup';
                END IF;
                END
                $$;
                CREATE TABLE {TABLE_NAME} AS SELECT * FROM {TABLE_NAME}_tmp;
                """,
        )

        drop_tmp = PostgresOperator(
            task_id="drop_tmp",
            sql=f"""
                DROP TABLE IF EXISTS {TABLE_NAME}_tmp;
                """,
        )

        drop_backup = PostgresOperator(
            task_id="drop_backup",
            sql=f"""
                DROP TABLE IF EXISTS {TABLE_NAME}_backup;
                """,
        )

        @task
        def done():
            return "New table is ready!"

        chain(
            create_tmp,
            load_data_into_tmp,
            test_tmp(),
            swap,
            drop_tmp,
            drop_backup,
            done(),
        )

        # define setup/ teardown relationship
        drop_tmp.as_teardown(setups=[create_tmp, load_data_into_tmp])
        drop_backup.as_teardown(setups=[swap])

        @task_group
        def validate():
            test_cols = SQLColumnCheckOperator(
                task_id="test_cols",
                retry_on_failure="True",
                table=f"{SCHEMA_NAME}.{TABLE_NAME}",
                column_mapping={
                    "petal_size_cm": {"min": {"geq_to": 5}, "max": {"leq_to": 10}},
                    "stem_length_cm": {"min": {"geq_to": 20}, "max": {"leq_to": 50}},
                    "leaf_size_cm": {"min": {"geq_to": 4}, "max": {"leq_to": 8}},
                },
                accept_none="True",
            )

            test_table = SQLTableCheckOperator(
                task_id="test_table",
                retry_on_failure="True",
                table=f"{SCHEMA_NAME}.{TABLE_NAME}",
                checks={
                    "row_count_check": {"check_statement": "COUNT(*) > 800"},
                    "at_least_20_tea_check": {
                        "check_statement": "COUNT(*) >= 20",
                        "partition_clause": "rose_type = 'tea'",
                    },
                    "month_check": {
                        "check_statement": "blooming_month IN ('April', 'May', 'June', 'July', 'August', 'September')"
                    },
                },
            )

            @task(trigger_rule="all_done")
            def sql_check_done():
                return "Additional data quality checks are done!"

            [test_cols, test_table] >> sql_check_done()

        swap >> validate()

    @task(
        outlets=[Dataset(f"postgres://{SCHEMA_NAME}/{TABLE_NAME}")],
    )
    def table_ready_for_the_model():
        return "The table is ready, modelling can begin!"

    chain(create_table(), table_ready_for_the_model())


create_rose_table()
