from config import get_config

from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute, Attribute, NUMBER
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.models import Model


class BooleanAsNumberAttribute(Attribute):
    """
    A class for boolean stored ast Number attributes
    """

    attr_type = NUMBER

    def serialize(self, value):
        if value is None:
            return None
        elif value:
            return '1'
        else:
            return '0'

    def deserialize(self, value):
        return bool(int(value))


class InstallationStateIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'state-index'
        projection = AllProjection()
        region = get_config().get('dynamodb', 'region')

    state = UnicodeAttribute(null=True, hash_key=True)


class InstallationBotStartedIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'bot_started-index'
        projection = AllProjection()
        region = get_config().get('dynamodb', 'region')

    bot_started = BooleanAsNumberAttribute(null=False, hash_key=True)


class Installation(Model):
    class Meta:
        table_name = get_config().get('dynamodb', 'installations_table')
        region = get_config().get('dynamodb', 'region')

    team_id = UnicodeAttribute(hash_key=True, null=False)
    bot_token = UnicodeAttribute(null=False)
    bot_token_expires_at = UTCDateTimeAttribute(null=True)  # Unix timestamp in UTC
    bot_started_index = InstallationBotStartedIndex()
    bot_started = BooleanAsNumberAttribute(null=False)
    state_index = InstallationStateIndex()
    state = UnicodeAttribute(null=True)


class ActiveAlertsStateIndex(GlobalSecondaryIndex):
    class Meta:
        index_name = 'state-index'
        projection = AllProjection()
        region = get_config().get('dynamodb', 'region')

    state = UnicodeAttribute(null=False, hash_key=True)


class ActiveAlerts(Model):
    class Meta:
        table_name = get_config().get('dynamodb', 'active_alerts_table')
        region = get_config().get('dynamodb', 'region')

    id = UnicodeAttribute(hash_key=True, null=False)
    state_index = ActiveAlertsStateIndex()
    state = UnicodeAttribute(null=False)
