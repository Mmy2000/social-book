# Generated by Django 4.2.16 on 2025-06-04 03:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0002_groupinvitation'),
        ('notifications', '0002_alter_notification_notification_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='group.group'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('like', 'Like'), ('comment', 'Comment'), ('reply', 'Reply'), ('comment_like', 'Comment Like'), ('friend_request', 'Friend Request'), ('friend_request_accepted', 'Friend Request Accepted'), ('friend_request_rejected', 'Friend Request Rejected'), ('friend_request_cancelled', 'Friend Request Cancelled'), ('group_invitation', 'Group Invitation'), ('group_invitation_accepted', 'Group Invitation Accepted'), ('group_invitation_declined', 'Group Invitation Declined')], max_length=50),
        ),
    ]
