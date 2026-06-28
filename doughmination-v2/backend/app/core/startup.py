"""
Copyright (c) 2026 Clove Twilight
Licensed under the ESAL-1.3 Licence.
See LICENCE.md in the project root for full licence information.
"""

"""
Application startup tasks
Initializes required data and performs setup
"""

from app.services.user_service import initialize_admin_user
from app.services.tag_service import initialize_default_tags
from app.services.status_service import initialize_status_storage
from app.services.bot_token_service import initialize_bot_token
from app.services.battery_key_service import initialize_battery_key
from app.services.battery_service import initialize_battery_storage

def startup_tasks():
    """
    Run all startup tasks in order
    These tasks ensure the application is properly configured
    """
    print("=" * 60)
    print("Starting Doughmination System Backend")
    print("=" * 60)
    
    # Initialize bot access token
    print("\n[1/6] Initializing bot access token...")
    bot_token = initialize_bot_token()

    # Initialize admin user
    print("\n[2/6] Initializing admin user...")
    initialize_admin_user()

    # Initialize member tags
    print("\n[3/6] Initializing member tags...")
    initialize_default_tags()

    # Initialize member status storage
    print("\n[4/6] Initializing member status storage...")
    initialize_status_storage()

    # Initialize battery access key
    print("\n[5/6] Initializing battery access key...")
    initialize_battery_key()

    # Initialize battery levels storage
    print("\n[6/6] Initializing battery levels storage...")
    initialize_battery_storage()
    
    print("\n" + "=" * 60)
    print("Startup complete! Server is ready.")
    print("=" * 60 + "\n")