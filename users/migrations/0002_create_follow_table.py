from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS users_follow (
                id BIGSERIAL PRIMARY KEY,
                created_at timestamp with time zone NOT NULL,
                follower_id bigint NOT NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED,
                followed_id bigint NOT NULL REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED,
                CONSTRAINT users_follow_unique UNIQUE (follower_id, followed_id)
            );
            """,
            reverse_sql="DROP TABLE IF EXISTS users_follow;"
        )
    ]
