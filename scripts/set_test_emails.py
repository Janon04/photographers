def set_test_emails():
from users.models import User
# Run these lines in the Django shell:
# from scripts.set_test_emails import set_test_emails; set_test_emails()
def set_test_emails():
    # Set emails for two test users (by username or id)
    # You can adjust the queries below as needed
    user1 = User.objects.filter(username='janon3030').first() or User.objects.filter(id=1).first()
    if user1:
        user1.email = 'janon3030@gmail.com'
        user1.save()
        print(f"Set email for {user1.username} to {user1.email}")
    else:
        print("User 'janon3030' not found.")
    user2 = User.objects.filter(username='djanonelhard').first() or User.objects.filter(id=2).first()
    if user2:
        user2.email = 'djanonelhard@gmail.com'
        user2.save()
        print(f"Set email for {user2.username} to {user2.email}")
    else:
        print("User 'djanonelhard' not found.")
