import logging
import getpass
from pyramid.settings import asbool

from .utils import hash_password
from .views import AccountIdGenerator


logger = logging.getLogger(__name__)


def create_user(env, username=None, password=None):
    """Administrative command to create a new user."""
    registry = env['registry']
    settings = registry.settings
    readonly_mode = asbool(settings.get('readonly', False))

    if readonly_mode:
        message = ('Cannot create a user with a readonly server.')
        logger.error(message)
        return 51

    if 'kinto.plugins.accounts' not in settings['includes']:
        message = ('Cannot create a user when the accounts plugin is not installed.')
        logger.error(message)
        return 52

    try:
        validator = AccountIdGenerator()
        if username is None:
            username = input('Username: ')
        while True:
            if not validator.match(username):
                print('{} is not a valid username.')
                print('Username should match {0!r}, please try again.'.format(validator.regexp))
                username = input('Username: ')
            else:
                break

        if password is None:
            while True:
                password = getpass.getpass('Please enter a password for {}: '.format(username))
                confirm = getpass.getpass('Please confirm the password: '.format(username))

                if password != confirm:
                    print('Sorry, passwords do not match, please try again.')
                else:
                    break
    except EOFError:
        print('User creation aborted')
        return 53

    print("Creating user '{}'".format(username))
    record = {'id': username, 'password': hash_password(password)}
    registry.storage.create(collection_id='account',
                            parent_id=username,
                            record=record,
                            ignore_conflict=True)
    registry.permission.add_principal_to_ace(
        '/accounts/{}'.format(username), 'write', 'account:{}'.format(username))

    return 0
