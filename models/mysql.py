# -*- coding: utf-8 -*-
import sqlalchemy
import config


class MySql:

    db_user = config.DB_USER
    db_pass = config.DB_PASSWORD
    db_name = config.DB_NAME
    cloud_sql_connection_name = config.DB_CONNECTION_NAME
    db = sqlalchemy.create_engine(
        sqlalchemy.engine.url.URL(
            drivername="mysql+pymysql",
            username=db_user,
            password=db_pass,
            database=db_name,
            query={"unix_socket": "/cloudsql/{}".format(cloud_sql_connection_name)},
        )
    )
