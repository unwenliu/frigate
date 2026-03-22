"""Peewee migrations -- 035_increase_cloud_fid_length.py.

Increase cloud_fid and cloud_dir_id field length from 64 to 128.

Some examples (model - class or model name)::

    > Model = migrator.orm['model_name']            # Return model in current state by name

    > migrator.sql(sql)                             # Run custom SQL
    > migrator.run(func, *args, **kwargs)           # Run python code
    > migrator.create_model(Model)                  # Create a model (could be used as decorator)
    > migrator.remove_model(model, cascade=True)    # Remove a model
    > migrator.add_fields(model, **fields)          # Add fields to a model
    > migrator.change_fields(model, **fields)       # Change fields
    > migrator.remove_fields(model, *field_names, cascade=True)
    > migrator.rename_field(model, old_field_name, new_field_name)
    > migrator.rename_table(model, new_table_name)
    > migrator.add_index(model, *col_names, unique=False)
    > migrator.drop_index(model, *col_names)
    > migrator.add_not_null(model, *field_names)
    > migrator.drop_not_null(model, *field_names)
    > migrator.add_default(model, field_name, default)

"""

import peewee as pw

from frigate.models import Recordings

SQL = pw.SQL


def migrate(migrator, database, fake=False, **kwargs):
    """Increase cloud_fid and cloud_dir_id field length."""
    # For SQLite, VARCHAR length is not enforced, so we just use change_fields
    # This updates the model definition without actual schema change
    # For MySQL/PostgreSQL, this would modify the column type
    migrator.change_fields(
        Recordings,
        cloud_fid=pw.CharField(max_length=128, null=True),
        cloud_dir_id=pw.CharField(max_length=128, null=True),
    )


def rollback(migrator, database, fake=False, **kwargs):
    """Revert cloud_fid and cloud_dir_id field length to 64."""
    # Note: rollback may fail if existing data exceeds 64 characters
    migrator.change_fields(
        Recordings,
        cloud_fid=pw.CharField(max_length=64, null=True),
        cloud_dir_id=pw.CharField(max_length=64, null=True),
    )
