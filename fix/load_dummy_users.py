import json
import os
from django.contrib.auth.models import User
from fix.models import Resident

def run():
    # Get the absolute path to dummy_users.json
    base_dir = os.path.dirname(__file__)
    json_path = os.path.join(base_dir, 'fixtures', 'dummy_users.json')

    with open(json_path, 'r') as f:
        data = json.load(f)

        for entry in data:
            # Skip if username already exists
            if User.objects.filter(username=entry['username']).exists():
                print(f"User {entry['username']} already exists. Skipping.")
                continue

            user = User.objects.create_user(
                username=entry['username'],
                password=entry['password'],
                first_name=entry.get('first_name', ''),
                last_name=entry.get('last_name', ''),
                email=entry['email']
            )

            Resident.objects.create(
                user=user,
                apartment_number=entry['apartment_number'],
                # phone_number=entry['phone_number']
            )
            print(f"Created user: {user.username}")
