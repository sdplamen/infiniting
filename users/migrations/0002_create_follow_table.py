from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Follow',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('follower', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='following',
                    to=settings.AUTH_USER_MODEL
                )),
                ('followed', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='followers',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'unique_together' :{('follower', 'followed')},
            },
        ),
    ]