##
# copyright 2009, James William Pye
# http://python.projects.postgresql.org
##
import sys
import os
import unittest

from .. import exceptions as pg_exc
from .. import unittest as pg_unittest

from ..driver import dbapi20 as dbapi20
from .. import driver as pg_driver

class test_connect(pg_unittest.TestCaseWithCluster):
	"""
	postgresql.driver *interface* tests.
	"""
	ip6 = '::1'
	ip4 = '127.0.0.1'
	host = 'localhost'
	params = {}

	def configure_cluster(self):
		super().configure_cluster()
		self.cluster.settings['log_min_messages'] = 'log'
		# Configure the hba file with the supported methods.
		with open(self.cluster.hba_file, 'w') as hba:
			hosts = ['0.0.0.0/0', '0::0/0',]
			methods = ['md5', 'crypt', 'password']
			for h in hosts:
				for m in methods:
					# user and method are the same name.
					hba.writelines(['host test {m} {h} {m}\n'.format(
						h = h,
						m = m
					)])
			# trusted
			hba.writelines(["host test trusted 0.0.0.0/0 trust\n"])
			hba.writelines(["host test trusted 0::0/0 trust\n"])
			# admin lines
			hba.writelines(["host all test 0.0.0.0/0 trust\n"])
			hba.writelines(["host all test 0::0/0 trust\n"])

	def initialize_database(self):
		super().initialize_database()
		with self.cluster.connection(user = 'test') as db:
			db.execute(
				"""
CREATE USER md5 WITH
	ENCRYPTED PASSWORD 'md5_password'
;

-- crypt doesn't work with encrypted passwords:
-- http://www.postgresql.org/docs/8.2/interactive/auth-methods.html#AUTH-PASSWORD
CREATE USER crypt WITH
	UNENCRYPTED PASSWORD 'crypt_password'
;

CREATE USER password WITH
	ENCRYPTED PASSWORD 'password_password'
;

CREATE USER trusted;
				"""
			)

	def test_dbapi_connect(self):
		host, port = self.cluster.address()
		MD5 = dbapi20.connect(
			user = 'md5',
			database = 'test',
			password = 'md5_password',
			host = host, port = port,
			**self.params
		)
		CRYPT = dbapi20.connect(
			user = 'crypt',
			database = 'test',
			password = 'crypt_password',
			host = host, port = port,
			**self.params
		)
		PASSWORD = dbapi20.connect(
			user = 'password',
			database = 'test',
			password = 'password_password',
			host = host, port = port,
			**self.params
		)
		TRUST = dbapi20.connect(
			user = 'trusted',
			database = 'test',
			password = '',
			host = host, port = port,
			**self.params
		)
		self.failUnlessEqual(MD5.cursor().execute('select 1').fetchone()[0], 1)
		self.failUnlessEqual(CRYPT.cursor().execute('select 1').fetchone()[0], 1)
		self.failUnlessEqual(PASSWORD.cursor().execute('select 1').fetchone()[0], 1)
		self.failUnlessEqual(TRUST.cursor().execute('select 1').fetchone()[0], 1)
		MD5.close()
		CRYPT.close()
		PASSWORD.close()
		TRUST.close()
		self.failUnlessRaises(pg_exc.ConnectionDoesNotExistError,
			MD5.cursor().execute, 'select 1'
		)

	def test_IP4_connect(self):
		C = pg_driver.IP4(
			user = 'test',
			host = '127.0.0.1',
			database = 'test',
			port = self.cluster.address()[1],
			**self.params
		)
		with C() as c:
			self.failUnlessEqual(c.prepare('select 1').first(), 1)

	def test_IP6_connect(self):
		C = pg_driver.IP6(
			user = 'test',
			host = '::1',
			database = 'test',
			port = self.cluster.address()[1],
			**self.params
		)
		with C() as c:
			self.failUnlessEqual(c.prepare('select 1').first(), 1)

	def test_Host_connect(self):
		C = pg_driver.Host(
			user = 'test',
			host = 'localhost',
			database = 'test',
			port = self.cluster.address()[1],
			**self.params
		)
		with C() as c:
			self.failUnlessEqual(c.prepare('select 1').first(), 1)

	def test_md5_connect(self):
		c = self.cluster.connection(
			user = 'md5',
			password = 'md5_password',
			database = 'test',
			**self.params
		)
		with c:
			self.failUnlessEqual(c.user, 'md5')

	def test_crypt_connect(self):
		c = self.cluster.connection(
			user = 'crypt',
			password = 'crypt_password',
			database = 'test',
			**self.params
		)
		with c:
			self.failUnlessEqual(c.user, 'crypt')

	def test_password_connect(self):
		c = self.cluster.connection(
			user = 'password',
			password = 'password_password',
			database = 'test',
		)
		with c:
			self.failUnlessEqual(c.user, 'password')

	def test_trusted_connect(self):
		c = self.cluster.connection(
			user = 'trusted',
			password = '',
			database = 'test',
			**self.params
		)
		with c:
			self.failUnlessEqual(c.user, 'trusted')

if __name__ == '__main__':
	unittest.main()