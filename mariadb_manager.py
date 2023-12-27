"""MariaDB 操作用Class"""
import mysql.connector
import base64


class MariaDBManager:
    def __init__(self, ssh_config, db_config):
        self.ssh_config = ssh_config
        self.db_config = db_config
        if ssh_config is not None:
            import sshtunnel
            self.server = sshtunnel.SSHTunnelForwarder(
                ssh_address_or_host=self.ssh_config["ssh_host"],
                ssh_username=self.ssh_config["ssh_username"],
                ssh_pkey=self.ssh_config["ssh_pkey"],
                remote_bind_address=self.ssh_config["remote_bind_address"]
            )
            self.server.start()

        self.connection = mysql.connector.connect(
            host=self.db_config["host"],
            port=(
                self.server.local_bind_port if ssh_config is not None else 3306
            ),
            user=self.db_config["user"],
            password=base64.b64decode(
                self.db_config["password_base64"]).decode("utf-8"),
            database=self.db_config["database"],
            charset=self.db_config["charset"]
        )

        self.cur = self.connection.cursor(dictionary=True)

    def close(self):
        if self.connection.is_connected():
            self.connection.close()

        if self.ssh_config is not None and self.server is not None:
            self.server.stop()

    def select(self, sql):
        self.cur.execute(sql)
        return self.cur.fetchall()
