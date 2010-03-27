# +--------------------------------------------------------------------------+
# |  Licensed Materials - Property of IBM                                    |
# |                                                                          |
# | (C) Copyright IBM Corporation 2009.                                      |
# +--------------------------------------------------------------------------+
# | This module complies with Django 1.0 and is                              |
# | Licensed under the Apache License, Version 2.0 (the "License");          |
# | you may not use this file except in compliance with the License.         |
# | You may obtain a copy of the License at                                  |
# | http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable |
# | law or agreed to in writing, software distributed under the License is   |
# | distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY |
# | KIND, either express or implied. See the License for the specific        |
# | language governing permissions and limitations under the License.        |
# +--------------------------------------------------------------------------+
# | Authors: Ambrish Bhargava, Tarun Pasrija, Rahul Priyadarshi              |
# +--------------------------------------------------------------------------+

from django.db.backends.creation import BaseDatabaseCreation
from django.conf import settings
from django.core.management import call_command
import types
from django import VERSION as djangoVersion

class DatabaseCreation(BaseDatabaseCreation):                
    data_types = { 
        'AutoField':                    'INTEGER GENERATED BY DEFAULT AS IDENTITY (START WITH 1, INCREMENT BY 1, CACHE 10 ORDER)', # DB2 Specific
        'BooleanField':                 'SMALLINT CHECK (%(attname)s IN (0,1))',
        'CharField':                    'VARCHAR(%(max_length)s)',
        'CommaSeparatedIntegerField':   'VARCHAR(%(max_length)s)',
        'DateField':                    'DATE',
        'DateTimeField':                'TIMESTAMP',
        'DecimalField':                 'DECIMAL(%(max_digits)s, %(decimal_places)s)',
        'FileField':                    'VARCHAR(%(max_length)s)',
        'FilePathField':                'VARCHAR(%(max_length)s)',
        'FloatField':                   'DOUBLE',
        'ImageField':                   'VARCHAR(%(max_length)s)',
        'IntegerField':                 'INTEGER',
        'BigIntegerField':              'BIGINT',
        'IPAddressField':               'VARCHAR(15)',
        'ManyToManyField':              'VARCHAR(%(max_length)s)',
        'NullBooleanField':             'SMALLINT CHECK (%(attname)s IN (0,1) OR (%(attname)s IS NULL))',
        'OneToOneField':                'VARCHAR(%(max_length)s)',
        'PhoneNumberField':             'VARCHAR(16)',
        'PositiveIntegerField':         'INTEGER CHECK (%(attname)s >= 0)',
        'PositiveSmallIntegerField':    'SMALLINT CHECK (%(attname)s >= 0)',
        'SlugField':                    'VARCHAR(%(max_length)s)',
        'SmallIntegerField':            'SMALLINT',
        'TextField':                    'CLOB',
        'TimeField':                    'TIME',
        'USStateField':                 'VARCHAR(2)',
        'URLField':                     'VARCHAR2(%(max_length)s)',
        'XMLField':                     'XML',
    }
        
    def sql_indexes_for_field(self, model, f, style):
        """Return the CREATE INDEX SQL statements for a single model field"""
        if f.db_index and not f.unique:
            qn = self.connection.ops.quote_name
            # ignore tablespace information
            tablespace_sql = ''
            output = [style.SQL_KEYWORD('CREATE INDEX') + ' ' +
                      style.SQL_TABLE(qn('%s_%s' % (model._meta.db_table, f.column))) + ' ' +
                      style.SQL_KEYWORD('ON') + ' ' +
                      style.SQL_TABLE(qn(model._meta.db_table)) + ' ' +
                      "(%s)" % style.SQL_FIELD(qn(f.column)) +
                      "%s;" % tablespace_sql]
        else:
            output = []
        return output
    
    # Method to prepare database. First we are deleting tables from the database,
    # then creating tables on the basis of installed models.
    def create_test_db(self, verbosity=0, autoclobber=None):
        print "Preparing Database..."
        if(djangoVersion[0:2] <= (1, 1)):
            if((isinstance(settings.TEST_DATABASE_NAME, types.StringType) or 
                isinstance(settings.TEST_DATABASE_NAME, types.UnicodeType)) and 
                (settings.TEST_DATABASE_NAME != '')):
                database = settings.TEST_DATABASE_NAME
            else:
                database = settings.DATABASE_NAME
            
            settings.DATABASE_SUPPORTS_TRANSACTIONS = True
        else:
            if((isinstance(self.connection.settings_dict["NAME"], types.StringType) or 
                isinstance(self.connection.settings_dict["NAME"], types.UnicodeType)) and 
                (self.connection.settings_dict["NAME"] != '')):
                database = self.connection.settings_dict["NAME"]
            else:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured("the database Name doesn't exist")
            self.connection.settings_dict["SUPPORTS_TRANSACTIONS"] = True
                
        self.__clean_up(self.connection.cursor())
        if(djangoVersion[0:2] <= (1, 1)):
            call_command('syncdb', verbosity=verbosity, interactive= False)
        else:
            call_command('syncdb', database=self.connection.alias, verbosity=verbosity, interactive= False)
        return database
    
    # Method to destroy database. Nothing is getting done over here.
    def destroy_test_db(self, test_database_name, verbosity=0):
        print "Destroying Database..."
        if(djangoVersion[0:2] <= (1, 1)):
            if((isinstance(settings.TEST_DATABASE_NAME, types.StringType) or 
                isinstance(settings.TEST_DATABASE_NAME, types.UnicodeType)) and 
                (settings.TEST_DATABASE_NAME != '')):
                database = settings.TEST_DATABASE_NAME
            else:
                database = settings.DATABASE_NAME
        else:
            if((isinstance(self.connection.settings_dict["NAME"], types.StringType) or 
                isinstance(self.connection.settings_dict["NAME"], types.UnicodeType)) and 
                (self.connection.settings_dict["NAME"] != '')):
                database = self.connection.settings_dict["NAME"]
            else:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured("database Name doesn't exist")
        
        return database
    
    # As DB2 does not allow to insert NULL value in UNIQUE col, hence modifing model.
    def sql_create_model(self, model, style, known_models=set()):
        for i in range(len(model._meta.local_fields)):
            if model._meta.local_fields[i].unique:
                model._meta.local_fields[i].null = False
                
            if len(model._meta.unique_together) != 0:
                if model._meta.local_fields[i].name in model._meta.unique_together[0]:
                    model._meta.local_fields[i].null = False
                
        return super(DatabaseCreation, self).sql_create_model(model, style, known_models)

    # Private method to clean up database.
    def __clean_up(self, cursor):
        #from django.db import connection
        tables = self.connection.introspection.django_table_names(only_existing=True)
        
        for table in tables:
            sql = "DROP TABLE %s" % self.connection.ops.quote_name(table)
            cursor.execute(sql)
        cursor.close()
