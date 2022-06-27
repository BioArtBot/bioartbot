"""
This script is populates the user database with a number of arbitrarily-named users for testing purposes.
This can be used to test frontend apps and API endpoints for creating, reading, updating, and deleteing users.
This script should not be used at all in production.

Usage:
After launching the docker container and migrating the database with `docker-compose exec artbot flask db upgrade`,
execute `docker-compose exec artbot python tests/seed_db.py` to fill the dev database with test users.
You may run the seed script as many times as you like. If a username already exists in the database, the script
will simply add 1 to the number at the end of the name until it hits a name that is not in use.

Note that this does not use the test database, but rather the dev database. So these users will be instantiated in
your development environment and won't be reset until you explicitly reset them, or restart your docker image.
A future version of this script will integrate with the test suite more closely, but for now this is a convenience
script for a largely manual process.
"""
import sys
sys.path.append("/usr/src/app") #works as long as this is the app home in Docker

from sqlalchemy.exc import IntegrityError, ProgrammingError
from web.app import create_app
from web.extensions import db
from web.api.user.user import SuperUser

def add_new_incremental_user(role,num):
    email = f'{role}{str(num)}@{role}.net'
    db_role = role.title()
    new_s_user = SuperUser.from_email(email,db_role)
    password = f'123456_{num}'
    new_s_user.set_password(password)
    return f'{email.ljust(25)} | {role.ljust(10)} | {password.ljust(10)}'

def seed_users(num_users = 10):
    app = create_app()
    app.config.from_object('web.settings.DevConfig')
    with app.app_context():
        msg = None
        for role in ['admin', 'printer']:
            print(f'Seeding {role} users:')
            print(f'{"email".ljust(25)} | {"role".ljust(10)} | password')
            for num in range(num_users):
                while msg is None:
                    try:
                        msg = add_new_incremental_user(role,num)
                        db.session.commit()
                        print(msg)
                    except IntegrityError:
                        db.session.rollback()
                        num += 1
                    except ProgrammingError:
                        raise Exception("Database is not configured for users.\n" +
                                        "Have you run `docker-compose exec artbot flask db upgrade`?"
                                        )
                msg = None
            print('-----------')
    print(f'Seeded {num_users} users for each role')


if __name__ == '__main__':
    seed_users()
