# Generated by Django 4.0.3 on 2022-03-22 06:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MatrixRoomModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room_id', models.CharField(max_length=512)),
            ],
        ),
        migrations.AddField(
            model_name='useraccountmodel',
            name='rooms',
            field=models.ManyToManyField(to='home.matrixroommodel'),
        ),
    ]